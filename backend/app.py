from __future__ import annotations
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from config import UPLOAD_DIR
from storage import (
    CaseRecord,
    save_case,
    list_cases_for_user,
    list_all_cases,
    load_all_cases_from_disk,
    append_chat,
    get_chat_history,
    append_feedback,
)
from pipeline.ocr import extract_text_from_file, normalize_text
from pipeline.analyzer import analyze_denial_text, to_json as analyzer_to_json
from pipeline.investigator import extract_evidence, to_json as investigator_to_json
from pipeline.evidence_accumulator import accumulate_evidence, to_json as evidence_agg_to_json
from pipeline.reasoning import reason_about_case, to_json as reasoning_to_json
from pipeline.confidence_calibrator import calibrate_confidence, to_json as confidence_to_json
from pipeline.adaptive_template import select_template, to_json as template_sel_to_json
from pipeline.advocate import generate_letter, template_options_json, LetterDraft
from pipeline.traceability import build_traceability_graph, to_json as trace_to_json
from pipeline import pattern_miner

from evaluation_engine import evaluate_system

from docx import Document
from reportlab.pdfgen import canvas

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = FastAPI(title="Lighthouse AI Backend – Novel Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_all_cases_from_disk()

# ----------------- Pydantic Models --------------------------------------

class UploadResponse(BaseModel):
    id: str
    user_id: str
    created_at: str
    denial_filename: Optional[str]
    medical_filename: Optional[str]
    denial_category: Optional[str]
    insurer_name: Optional[str]
    confidence_score: Optional[float]
    status: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class GenerateLetterRequest(BaseModel):
    user_id: str
    case_id: str
    template_id: str
    format: str  # txt | docx | pdf

class FeedbackRequest(BaseModel):
    user_id: str
    case_id: str
    target_type: str  # 'letter' or 'evidence'
    target_id: str
    label: str  # 'up' or 'down'
    comment: Optional[str] = None

class SimulateRequest(BaseModel):
    user_id: str
    case_id: str
    hypothetical_evidence: str

# ----------------- Helpers ----------------------------------------------

def _safe_filename(prefix: str, original: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ts}_{(original or prefix).replace(' ', '_')}"

# ----------------- Routes: Upload & Pipeline ----------------------------

@app.post("/api/upload", response_model=UploadResponse)
async def upload_case(
    user_id: str = Form(...),
    denial_letter: Optional[UploadFile] = File(None),
    medical_record: Optional[UploadFile] = File(None),
):
    if not denial_letter and not medical_record:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    case_id = f"case_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    denial_path: Optional[Path] = None
    medical_path: Optional[Path] = None

    if denial_letter:
        fn = _safe_filename("denial", denial_letter.filename)
        denial_path = UPLOAD_DIR / fn
        with open(denial_path, "wb") as f:
            f.write(await denial_letter.read())

    if medical_record:
        fn = _safe_filename("medical", medical_record.filename)
        medical_path = UPLOAD_DIR / fn
        with open(medical_path, "wb") as f:
            f.write(await medical_record.read())

    # Phase 1: OCR + normalization
    denial_text = normalize_text(extract_text_from_file(denial_path)) if denial_path else ""
    medical_text = normalize_text(extract_text_from_file(medical_path)) if medical_path else ""

    # Phase 2: Analyzer
    if not denial_text:
        from pipeline.analyzer import DenialAnalysis
        analysis = DenialAnalysis(
            denial_reason_raw="Denial letter could not be parsed.",
            denial_category="Administrative",
            insurer_name=None,
            denial_code=None,
            category_scores={"Administrative": 1.0},
        )
    else:
        analysis = analyze_denial_text(denial_text)

    # Phase 3: Investigator
    evidence_bundle = extract_evidence(medical_text, analysis.denial_category, analysis.denial_reason_raw)

    # Phase 4: Evidence Accumulation
    evidence_agg = accumulate_evidence(evidence_bundle)

    # Phase 5: Reasoning Engine
    reasoning = reason_about_case(
        analysis.denial_category,
        analysis.denial_reason_raw,
        evidence_agg,
    )

    # Phase 6: Confidence Calibration
    calibrated = calibrate_confidence(reasoning, evidence_agg, analysis)

    # Track patterns for research metrics
    pattern_miner.update_patterns_on_case(analysis.denial_category, reasoning)

    # Phase 7: Adaptive Template Selection
    template_sel = select_template(analysis.denial_category, calibrated)

    # Phase 8: Advocate (auto-draft if recommended)
    letter: LetterDraft | None = None
    if calibrated.recommended_action == "AUTO_DRAFT":
        letter = generate_letter(
            template_id=template_sel.template_id,
            denial_category=analysis.denial_category,
            denial_reason=analysis.denial_reason_raw,
            insurer_name=analysis.insurer_name,
            evidence_snippets="\n".join([e.text for e in evidence_bundle.evidence_items][:40]),
            reasoning_summary=reasoning.reasoning_summary,
            tone=template_sel.tone,
            length=template_sel.length,
        )

    # Phase 9: Traceability Graph
    trace_graph = build_traceability_graph(case_id, analysis, evidence_bundle, reasoning, letter)

    record = CaseRecord(
        id=case_id,
        user_id=user_id,
        created_at=datetime.utcnow().isoformat() + "Z",
        denial_filename=denial_letter.filename if denial_letter else None,
        medical_filename=medical_record.filename if medical_record else None,
        denial_category=analysis.denial_category,
        insurer_name=analysis.insurer_name,
        confidence_score=calibrated.calibrated_score,
        status="processed",
        denial_reason_raw=analysis.denial_reason_raw,
        reasoning_summary=reasoning.reasoning_summary,
        evidence_summary=evidence_bundle.summary,
        letter_text=letter.letter_text if letter else None,
        denial_text=denial_text,
        medical_text=medical_text,
        analyzer_output=analyzer_to_json(analysis),
        investigator_output=investigator_to_json(evidence_bundle),
        evidence_aggregate=evidence_agg_to_json(evidence_agg),
        reasoning_output=reasoning_to_json(reasoning),
        confidence_output=confidence_to_json(calibrated),
        template_metadata=template_sel_to_json(template_sel),
        trace_graph=trace_to_json(trace_graph),
    )
    save_case(record)

    return UploadResponse(
        id=record.id,
        user_id=record.user_id,
        created_at=record.created_at,
        denial_filename=record.denial_filename,
        medical_filename=record.medical_filename,
        denial_category=record.denial_category,
        insurer_name=record.insurer_name,
        confidence_score=record.confidence_score,
        status=record.status,
    )


# --- evaluation metrics --- 

@app.get("/api/evaluation")
def get_evaluation():
    return evaluate_system()

# ----------------- History & Templates ----------------------------------

@app.get("/api/history")
def get_history(user_id: str):
    cases = list_cases_for_user(user_id)
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "created_at": c.created_at,
            "denial_filename": c.denial_filename,
            "medical_filename": c.medical_filename,
            "denial_category": c.denial_category,
            "insurer_name": c.insurer_name,
            "confidence_score": c.confidence_score,
            "status": c.status,
        }
        for c in cases
    ]

@app.get("/api/chat/history")
def chat_history(user_id: str):
    return get_chat_history(user_id)

@app.get("/api/template-options")
def template_options():
    return template_options_json()

# ----------------- Chatbot (using new artifacts) ------------------------

@app.post("/api/chat", response_model=ChatMessage)
def chat(req: ChatRequest):
    append_chat(req.user_id, "user", req.message)
    cases = list_cases_for_user(req.user_id)
    latest = cases[0] if cases else None

    if not latest:
        answer = (
            "You haven't uploaded any denial letters or medical records yet.\n\n"
            "Please upload them so I can analyze the denial, extract evidence, and draft an appeal."
        )
    else:
        q = req.message.lower()
        denial = latest.analyzer_output or {}
        evidence = latest.investigator_output or {}
        confidence = latest.confidence_output or {}
        reasoning = latest.reasoning_output or {}

        if "why" in q and "denied" in q:
            answer = (
                f"Your claim was denied in the category {latest.denial_category}.\n\n"
                f"🧾 Insurer: {latest.insurer_name or 'Not clearly specified'}\n"
                f"📄 Exact denial reason:\n"
                f"\"{latest.denial_reason_raw}\"\n\n"
                f"Internal category scoring: {denial.get('category_scores', {})}"
            )
        elif "evidence" in q or "medical" in q:
            ev_items = evidence.get("evidence_items", [])
            if not ev_items:
                answer = (
                    "I could not find structured medical evidence that strongly supports this appeal.\n"
                    "You may need additional clinical documentation (e.g., severity notes, failed prior therapies)."
                )
            else:
                top = ev_items[:5]
                lines = []
                for e in top:
                    lines.append(
                        f"- [{e['evidence_type']}] {e['text']} "
                        f"(confidence {e['confidence']:.2f})"
                    )
                answer = (
                    "Here are key evidence snippets I found in your medical records:\n\n"
                    + "\n".join(lines)
                    + "\n\nThese were used to support the appeal reasoning."
                )
        elif "chance" in q or "success" in q or "appeal" in q:
            score = confidence.get("calibrated_score", latest.confidence_score or 0)
            bucket = confidence.get("bucket", "UNKNOWN")
            decision = confidence.get("recommended_action", "NEEDS_REVIEW")
            answer = (
                f"Based on your documents, the calibrated success indication is {bucket}.\n\n"
                f"📊 Calibrated Confidence Score: {score:.0f}%\n"
                f"🧭 Recommended action: {decision}\n\n"
                f"Reasoning summary:\n{latest.reasoning_summary}"
            )
        elif "graph" in q or "trace" in q or "explain" in q:
            graph = latest.trace_graph or {}
            n_nodes = len(graph.get("nodes", []))
            n_edges = len(graph.get("edges", []))
            answer = (
                "I maintain a traceability graph for your case so that every appeal point can be linked "
                "back to specific evidence.\n\n"
                f"Current graph: **{n_nodes} nodes and {n_edges} edges.\n"
                "Nodes include the denial case, evidence snippets, the reasoning engine, and the appeal letter."
            )
        else:
            answer = (
                "This is your private Lighthouse AI assistant.\n\n"
                "You can ask things like:\n"
                "• Why was my claim denied?\n"
                "• What medical evidence supports my appeal?\n"
                "• What is the success chance of my appeal?\n"
                "• Show how the system traces evidence to the letter."
            )

    msg = append_chat(req.user_id, "bot", answer)
    return ChatMessage(**msg)

# ----------------- Letter Generation ------------------------------------

@app.post("/api/generate-letter")
def generate_letter_endpoint(req: GenerateLetterRequest):
    cases = list_cases_for_user(req.user_id)
    case = next((c for c in cases if c.id == req.case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    t_id = req.template_id
    letter = generate_letter(
        template_id=t_id,
        denial_category=case.denial_category or "",
        denial_reason=case.denial_reason_raw or "",
        insurer_name=case.insurer_name,
        evidence_snippets=case.evidence_summary or "",
        reasoning_summary=case.reasoning_summary or "",
    )
    content = letter.letter_text

    fmt = req.format.lower()
    if fmt == "txt":
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=appeal.txt"},
        )
    if fmt == "docx":
        buffer = io.BytesIO()
        doc = Document()
        for line in content.splitlines():
            doc.add_paragraph(line)
        doc.save(buffer)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=appeal.docx"},
        )
    if fmt == "pdf":
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        text_obj = p.beginText(50, 800)
        for line in content.splitlines():
            text_obj.textLine(line)
        p.drawText(text_obj)
        p.showPage()
        p.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=appeal.pdf"},
        )
    raise HTTPException(status_code=400, detail="Unsupported format")

# ----------------- Feedback (Active Learning Hook) ----------------------

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    entry = req.dict()
    append_feedback(entry)
    return {"status": "ok"}

# ----------------- Simulation (What-If) ---------------------------------

@app.post("/api/simulate")
def simulate_case(req: SimulateRequest):
    cases = list_cases_for_user(req.user_id)
    case = next((c for c in cases if c.id == req.case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Very simple: treat hypothetical evidence as extra severity/failed/risk text
    from pipeline.evidence_accumulator import EvidenceAggregate
    from pipeline.reasoning import reason_about_case
    from pipeline.confidence_calibrator import calibrate_confidence
    from pipeline.analyzer import DenialAnalysis

    # Construct a fake EvidenceAggregate boost
    base_agg_dict = case.evidence_aggregate or {}
    agg = EvidenceAggregate(
        total_items=base_agg_dict.get("total_items", 0) + 2,
        by_type=base_agg_dict.get("by_type", {}),
        avg_confidence=base_agg_dict.get("avg_confidence", 0.7),
        severity_score=base_agg_dict.get("severity_score", 0.0) + 1.5,
        failed_therapy_score=base_agg_dict.get("failed_therapy_score", 0.0) + 2.0,
        risk_score=base_agg_dict.get("risk_score", 0.0) + 1.0,
    )

    analysis_dict = case.analyzer_output or {}
    analysis = DenialAnalysis(
        denial_reason_raw=analysis_dict.get("denial_reason_raw", case.denial_reason_raw or ""),
        denial_category=analysis_dict.get("denial_category", case.denial_category or "Administrative"),
        insurer_name=analysis_dict.get("insurer_name"),
        denial_code=analysis_dict.get("denial_code"),
        category_scores=analysis_dict.get("category_scores", {}),
    )

    reasoning = reason_about_case(analysis.denial_category, analysis.denial_reason_raw, agg)
    calibrated = calibrate_confidence(reasoning, agg, analysis)

    return {
        "simulated_score": calibrated.calibrated_score,
        "bucket": calibrated.bucket,
        "recommended_action": calibrated.recommended_action,
        "hypothetical_evidence": req.hypothetical_evidence,
    }

# ----------------- Analytics & Matplotlib Dashboard ---------------------

@app.get("/api/analytics/summary")
def analytics_summary():
    metrics = pattern_miner.get_global_metrics()
    cases = list_all_cases()
    return {
        "global_patterns": metrics,
        "total_cases": len(cases),
        "avg_confidence": (
            sum((c.confidence_score or 0) for c in cases) / len(cases) if cases else 0.0
        ),
    }

@app.get("/api/analytics/plot")
def analytics_plot():
    metrics = pattern_miner.get_global_metrics()
    cats = list(metrics.get("categories", {}).keys())
    counts = [metrics["categories"][c]["count"] for c in cats] if cats else []

    fig, ax = plt.subplots()
    if cats:
        ax.bar(cats, counts)
        ax.set_ylabel("Cases")
        ax.set_xlabel("Denial Category")
        ax.set_title("Cases per Denial Category")
        plt.xticks(rotation=20, ha="right")
    else:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")