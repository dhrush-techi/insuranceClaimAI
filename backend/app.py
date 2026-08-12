from __future__ import annotations
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from config import UPLOAD_DIR
from storage import (
    CaseRecord,
    save_case,
    get_case_by_id,
    list_cases_for_user,
    list_all_cases,
    load_all_cases_from_disk,
    append_chat,
    get_chat_history,
    append_feedback,
)
from pipeline.ocr import extract_text_from_file, normalize_text, ingest_document
from pipeline.analyzer import analyze_denial_text, to_json as analyzer_to_json
from pipeline.investigator import extract_evidence, to_json as investigator_to_json
from pipeline.evidence_accumulator import accumulate_evidence, to_json as evidence_agg_to_json
from pipeline.reasoning import reason_about_case, to_json as reasoning_to_json
from pipeline.confidence_calibrator import calibrate_confidence, to_json as confidence_to_json
from pipeline.adaptive_template import select_template, to_json as template_sel_to_json
from pipeline.advocate import generate_letter, template_options_json, LetterDraft
from pipeline.traceability import build_traceability_graph, to_json as trace_to_json
from pipeline.chatbot import answer_case_query
from pipeline import pattern_miner

from evaluation_engine import evaluate_system
from evaluation.runner import run_evaluation_suite, EVAL_OUTPUT_DIR
import json

from docx import Document
from reportlab.pdfgen import canvas
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = FastAPI(title="Lighthouse AI Backend – Medical Insurance Appeal System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_all_cases_from_disk()

# ----------------- Pydantic Models --------------------------------------

class CaseCreateRequest(BaseModel):
    user_id: str
    patient_identifier: Optional[str] = None

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

class EvaluationRunRequest(BaseModel):
    experiment_id: str = "exp_001"

# ----------------- Helpers ----------------------------------------------

def _safe_filename(prefix: str, original: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ts}_{(original or prefix).replace(' ', '_')}"

def _process_case_pipeline(case_record: CaseRecord, denial_path: Optional[Path], medical_path: Optional[Path]) -> CaseRecord:
    # Phase 1: Ingestion & OCR
    denial_ingest = ingest_document(denial_path, "doc_denial") if denial_path else None
    medical_ingest = ingest_document(medical_path, "doc_medical") if medical_path else None

    denial_text = denial_ingest.full_text if denial_ingest else ""
    medical_text = medical_ingest.full_text if medical_ingest else ""
    ocr_quality = medical_ingest.overall_ocr_quality if medical_ingest else 0.90

    # Phase 2: Analyzer Agent
    analysis = analyze_denial_text(denial_text)

    # Phase 3: Investigator Agent
    evidence_bundle = extract_evidence(
        medical_text,
        analysis.denial_category,
        analysis.denial_reason_raw,
        document_id=medical_ingest.document_id if medical_ingest else "doc_medical",
        pages_data=[{"page_number": p.page_number, "char_start": p.char_start, "char_end": p.char_end} for p in (medical_ingest.pages if medical_ingest else [])]
    )

    # Phase 4: Evidence Accumulator
    evidence_agg = accumulate_evidence(evidence_bundle)

    # Phase 5 & 7: Reasoning Engine
    reasoning = reason_about_case(
        analysis.denial_category,
        analysis.denial_reason_raw,
        evidence_agg,
    )

    # Phase 6: Confidence Calibration
    calibrated = calibrate_confidence(reasoning, evidence_agg, analysis, ocr_quality=ocr_quality)
    pattern_miner.update_patterns_on_case(analysis.denial_category, reasoning)

    # Phase 8: Adaptive Template Selection
    template_sel = select_template(analysis.denial_category, calibrated)

    # Phase 9: Advocate Agent (Auto-Draft if recommended)
    letter: Optional[LetterDraft] = None
    if calibrated.recommended_action == "AUTO_DRAFT":
        letter = generate_letter(
            template_id=template_sel.template_id,
            denial_category=analysis.denial_category,
            denial_reason=analysis.denial_reason_raw,
            insurer_name=analysis.insurer_name,
            evidence_snippets=evidence_bundle.summary,
            reasoning_summary=reasoning.reasoning_summary,
            evidence_items=[item.__dict__ for item in evidence_bundle.evidence_items],
        )

    # Phase 5: Traceability AKG
    trace_graph = build_traceability_graph(case_record.id, analysis, evidence_bundle, reasoning, letter)

    case_record.denial_category = analysis.denial_category
    case_record.insurer_name = analysis.insurer_name
    case_record.confidence_score = calibrated.calibrated_score
    case_record.status = "processed"
    case_record.denial_reason_raw = analysis.denial_reason_raw
    case_record.reasoning_summary = reasoning.reasoning_summary
    case_record.evidence_summary = evidence_bundle.summary
    case_record.letter_text = letter.letter_text if letter else None
    case_record.denial_text = denial_text
    case_record.medical_text = medical_text

    case_record.analyzer_output = analyzer_to_json(analysis)
    case_record.investigator_output = investigator_to_json(evidence_bundle)
    case_record.evidence_aggregate = evidence_agg_to_json(evidence_agg)
    case_record.reasoning_output = reasoning_to_json(reasoning)
    case_record.confidence_output = confidence_to_json(calibrated)
    case_record.template_metadata = template_sel_to_json(template_sel)
    case_record.trace_graph = trace_to_json(trace_graph)

    save_case(case_record)
    return case_record

# ----------------- Required API Endpoints -------------------------------

@app.post("/api/cases")
async def create_case(req: CaseCreateRequest):
    case_id = f"case_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    case_record = CaseRecord(
        id=case_id,
        user_id=req.user_id,
        created_at=datetime.utcnow().isoformat() + "Z",
        denial_filename=None,
        medical_filename=None,
        denial_category=None,
        insurer_name=None,
        confidence_score=None,
        status="pending",
        denial_reason_raw=None,
        reasoning_summary=None,
        evidence_summary=None,
        letter_text=None,
        denial_text="",
        medical_text="",
    )
    save_case(case_record)
    return {"case_id": case_id, "status": "created"}

@app.post("/api/cases/{case_id}/documents")
async def upload_case_documents(
    case_id: str,
    user_id: str = Form(...),
    denial_letter: Optional[UploadFile] = File(None),
    medical_record: Optional[UploadFile] = File(None),
):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    denial_path: Optional[Path] = None
    medical_path: Optional[Path] = None

    if denial_letter:
        fn = _safe_filename("denial", denial_letter.filename)
        denial_path = UPLOAD_DIR / fn
        with open(denial_path, "wb") as f:
            f.write(await denial_letter.read())
        case.denial_filename = denial_letter.filename

    if medical_record:
        fn = _safe_filename("medical", medical_record.filename)
        medical_path = UPLOAD_DIR / fn
        with open(medical_path, "wb") as f:
            f.write(await medical_record.read())
        case.medical_filename = medical_record.filename

    processed = _process_case_pipeline(case, denial_path, medical_path)
    return UploadResponse(
        id=processed.id,
        user_id=processed.user_id,
        created_at=processed.created_at,
        denial_filename=processed.denial_filename,
        medical_filename=processed.medical_filename,
        denial_category=processed.denial_category,
        insurer_name=processed.insurer_name,
        confidence_score=processed.confidence_score,
        status=processed.status,
    )

@app.post("/api/cases/{case_id}/process")
async def process_case_endpoint(case_id: str):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return {"case_id": case_id, "status": case.status, "confidence_score": case.confidence_score}

@app.get("/api/cases/{case_id}")
async def get_case_details(case_id: str):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case

@app.get("/api/cases/{case_id}/analysis")
async def get_case_analysis(case_id: str):
    case = get_case_by_id(case_id)
    if not case or not case.analyzer_output:
        raise HTTPException(status_code=404, detail="Analysis not found for this case.")
    return case.analyzer_output

@app.get("/api/cases/{case_id}/evidence")
async def get_case_evidence(case_id: str):
    case = get_case_by_id(case_id)
    if not case or not case.investigator_output:
        raise HTTPException(status_code=404, detail="Evidence not found for this case.")
    return case.investigator_output

@app.get("/api/cases/{case_id}/graph")
async def get_case_graph(case_id: str):
    case = get_case_by_id(case_id)
    if not case or not case.trace_graph:
        raise HTTPException(status_code=404, detail="Graph not found for this case.")
    return case.trace_graph

@app.get("/api/cases/{case_id}/confidence")
async def get_case_confidence(case_id: str):
    case = get_case_by_id(case_id)
    if not case or not case.confidence_output:
        raise HTTPException(status_code=404, detail="Confidence calibration not found for this case.")
    return case.confidence_output

@app.get("/api/cases/{case_id}/appeal")
async def get_case_appeal(case_id: str):
    case = get_case_by_id(case_id)
    if not case or not case.letter_text:
        raise HTTPException(status_code=404, detail="Appeal letter draft not available for this case.")
    return {"case_id": case_id, "letter_text": case.letter_text}

@app.post("/api/cases/{case_id}/chat")
async def chat_with_case(case_id: str, req: ChatRequest):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    append_chat(req.user_id, "user", req.message)

    inv_output = case.investigator_output or {}
    evidence_raw = inv_output.get("evidence_items", [])
    
    from pipeline.investigator import EvidenceItem
    evidence_items = [
        EvidenceItem(
            evidence_id=item["evidence_id"],
            document_id=item.get("document_id", "doc_001"),
            page=item.get("page", 1),
            text=item["text"],
            evidence_type=item["evidence_type"],
            start_char=item.get("start_char", 0),
            end_char=item.get("end_char", 0),
            score=item.get("score", 0.80),
            confidence=item.get("confidence", 0.80),
        )
        for item in evidence_raw
    ]

    res = answer_case_query(req.message, evidence_items, denial_category=case.denial_category)
    append_chat(req.user_id, "assistant", res.answer)

    return {
        "reply": res.answer,
        "citations": res.citations,
        "confidence_score": res.confidence_score,
    }

# ----------------- Evaluation APIs --------------------------------------

@app.post("/api/evaluation/run")
async def run_evaluation_endpoint(req: EvaluationRunRequest):
    report = run_evaluation_suite(req.experiment_id)
    return report

@app.get("/api/evaluation/results")
async def get_evaluation_results(experiment_id: str = "exp_001"):
    path = EVAL_OUTPUT_DIR / experiment_id / "aggregate_results.json"
    if not path.exists():
        return {
            "experiment_id": experiment_id,
            "status": "N/A — experiment not yet executed",
            "message": "Run POST /api/evaluation/run first."
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/evaluation/report")
async def get_evaluation_report():
    return evaluate_system()

# ----------------- Existing Direct Upload Endpoint ---------------------

@app.post("/api/upload", response_model=UploadResponse)
async def upload_case_direct(
    user_id: str = Form(...),
    denial_letter: Optional[UploadFile] = File(None),
    medical_record: Optional[UploadFile] = File(None),
):
    if not denial_letter and not medical_record:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    case_id = f"case_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    case = CaseRecord(
        id=case_id,
        user_id=user_id,
        created_at=datetime.utcnow().isoformat() + "Z",
        denial_filename=denial_letter.filename if denial_letter else None,
        medical_filename=medical_record.filename if medical_record else None,
        denial_category=None,
        insurer_name=None,
        confidence_score=None,
        status="pending",
        denial_reason_raw=None,
        reasoning_summary=None,
        evidence_summary=None,
        letter_text=None,
        denial_text="",
        medical_text="",
    )

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

    processed = _process_case_pipeline(case, denial_path, medical_path)
    return UploadResponse(
        id=processed.id,
        user_id=processed.user_id,
        created_at=processed.created_at,
        denial_filename=processed.denial_filename,
        medical_filename=processed.medical_filename,
        denial_category=processed.denial_category,
        insurer_name=processed.insurer_name,
        confidence_score=processed.confidence_score,
        status=processed.status,
    )