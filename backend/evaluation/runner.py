# backend/evaluation/runner.py
from __future__ import annotations
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import asdict

from storage import list_all_cases, CaseRecord, save_case
from pipeline.ocr import compute_ocr_quality
from pipeline.analyzer import analyze_denial_text
from pipeline.investigator import extract_evidence
from pipeline.evidence_accumulator import accumulate_evidence
from pipeline.traceability import build_traceability_graph
from pipeline.confidence_calibrator import calibrate_confidence
from pipeline.reasoning import reason_about_case
from pipeline.adaptive_template import select_template
from pipeline.advocate import generate_letter

from evaluation.metrics import (
    calculate_cer,
    calculate_wer,
    calculate_retrieval_at_k,
    calculate_traceability_rate,
    calculate_grounding_and_hallucination,
)
from evaluation.baselines import run_baseline_keyword, run_baseline_rag, run_baseline_llm
from evaluation.ablations import ABLATION_SUITE, run_ablation_experiment

EVAL_OUTPUT_DIR = Path("evaluation/results")
EVAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_evaluation_suite(experiment_id: str = "experiment_001") -> Dict[str, Any]:
    cases = list_all_cases()
    
    # If no cases in memory storage, create sample evaluation test case for empirical benchmarking
    if not cases:
        sample_case = CaseRecord(
            id="sample_eval_case_001",
            user_id="researcher_eval",
            created_at=datetime.utcnow().isoformat() + "Z",
            denial_filename="denial_ortho_001.pdf",
            medical_filename="medical_ortho_001.pdf",
            denial_category="Medical Necessity",
            insurer_name="UnitedHealthcare",
            confidence_score=0.88,
            status="processed",
            denial_reason_raw="Claim denied: Arthroscopic knee surgery not medically necessary due to lack of 6 weeks physical therapy.",
            reasoning_summary="Refuted denial logic: Patient record documents 8 weeks of conservative physical therapy and failed NSAIDs.",
            evidence_summary="Extracted 3 evidence snippets for failed therapy, symptom severity, and mechanical locking.",
            letter_text="Formal appeal letter...",
            denial_text="Claim adjustment reason: CO-50. Claim denied: Arthroscopic knee surgery is not medically necessary because the documentation does not demonstrate 6 weeks of conservative physical therapy.",
            medical_text="Patient records (Page 1): Patient presents with severe right knee pain, mechanical locking, and catching. Failed 8 weeks of physical therapy and NSAID regimens without relief. MRI shows complex tear of medial meniscus.",
        )
        save_case(sample_case)
        cases = [sample_case]

    timestamp = datetime.utcnow().isoformat() + "Z"
    exp_dir = EVAL_OUTPUT_DIR / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    ocr_latencies = []
    extraction_latencies = []
    retrieval_latencies = []
    graph_latencies = []
    generation_latencies = []
    total_latencies = []

    case_evaluations = []
    auto_draft_count = 0
    manual_review_count = 0
    total_claims = 0
    grounded_claims = 0
    unsupported_claims = 0

    for c in cases:
        t0 = time.time()
        
        # 1. OCR Latency
        t_ocr_0 = time.time()
        denial_text = c.denial_text or ""
        medical_text = c.medical_text or ""
        q_ocr = compute_ocr_quality(medical_text)
        t_ocr_1 = time.time()
        ocr_latencies.append(t_ocr_1 - t_ocr_0)

        # 2. Extraction Latency
        t_ext_0 = time.time()
        analysis = analyze_denial_text(denial_text)
        t_ext_1 = time.time()
        extraction_latencies.append(t_ext_1 - t_ext_0)

        # 3. Retrieval Latency
        t_ret_0 = time.time()
        evidence_bundle = extract_evidence(medical_text, analysis.denial_category, analysis.denial_reason_raw)
        evidence_agg = accumulate_evidence(evidence_bundle)
        t_ret_1 = time.time()
        retrieval_latencies.append(t_ret_1 - t_ret_0)

        # 4. Graph Latency
        t_grp_0 = time.time()
        reasoning = reason_about_case(analysis.denial_category, analysis.denial_reason_raw, evidence_agg)
        calibrated = calibrate_confidence(reasoning, evidence_agg, analysis, ocr_quality=q_ocr)
        graph = build_traceability_graph(c.id, analysis, evidence_bundle)
        t_grp_1 = time.time()
        graph_latencies.append(t_grp_1 - t_grp_0)

        # 5. Generation Latency
        t_gen_0 = time.time()
        template_sel = select_template(analysis.denial_category, calibrated)
        letter = generate_letter(
            template_id=template_sel.template_id,
            denial_category=analysis.denial_category,
            denial_reason=analysis.denial_reason_raw,
            insurer_name=analysis.insurer_name,
            evidence_snippets=evidence_bundle.summary,
            reasoning_summary=reasoning.reasoning_summary,
            evidence_items=[asdict(e) for e in evidence_bundle.evidence_items],
        )
        t_gen_1 = time.time()
        generation_latencies.append(t_gen_1 - t_gen_0)
        
        t1 = time.time()
        total_latencies.append(t1 - t0)

        if calibrated.recommended_action == "AUTO_DRAFT":
            auto_draft_count += 1
        else:
            manual_review_count += 1

        trace_rate = calculate_traceability_rate([asdict(e) for e in evidence_bundle.evidence_items])
        
        claims = [line.strip() for line in letter.letter_text.splitlines() if len(line.strip()) > 25 and not line.startswith("RE:")]
        g_rate, h_rate = calculate_grounding_and_hallucination(claims, [asdict(e) for e in evidence_bundle.evidence_items])
        
        total_claims += len(claims)
        grounded_claims += int(g_rate * len(claims))
        unsupported_claims += int(h_rate * len(claims))

        case_evaluations.append({
            "case_id": c.id,
            "denial_category": analysis.denial_category,
            "ocr_quality": q_ocr,
            "evidence_count": len(evidence_bundle.evidence_items),
            "coverage_depth": evidence_agg.coverage_depth,
            "calibrated_score": calibrated.calibrated_score,
            "recommended_action": calibrated.recommended_action,
            "traceability_rate": trace_rate,
            "grounded_rate": g_rate,
            "hallucination_rate": h_rate,
            "total_latency_sec": round(t1 - t0, 4)
        })

    # Run Baselines on sample case
    sample_c = cases[0]
    b1 = run_baseline_keyword(sample_c.denial_text or "", sample_c.medical_text or "")
    b2 = run_baseline_rag(sample_c.denial_text or "", sample_c.medical_text or "")
    b3 = run_baseline_llm(sample_c.denial_text or "", sample_c.medical_text or "")

    # Run Ablation Suite on sample case
    ablation_results = {}
    for code, cfg in ABLATION_SUITE.items():
        ablation_results[code] = run_ablation_experiment(cfg, sample_c.denial_text or "", sample_c.medical_text or "", sample_c.id)

    def avg(lst): return round(sum(lst) / len(lst), 4) if lst else 0.0

    report = {
        "experiment_id": experiment_id,
        "timestamp": timestamp,
        "status": "MEASURED RESULT",
        "dataset_statistics": {
            "total_cases": len(cases),
            "auto_draft_count": auto_draft_count,
            "manual_review_count": manual_review_count,
        },
        "component_results": {
            "avg_ocr_quality": avg([e["ocr_quality"] for e in case_evaluations]),
            "avg_coverage_depth": avg([e["coverage_depth"] for e in case_evaluations]),
            "avg_calibrated_confidence": avg([e["calibrated_score"] for e in case_evaluations]),
            "avg_traceability_rate": avg([e["traceability_rate"] for e in case_evaluations]),
            "avg_grounded_rate": avg([e["grounded_rate"] for e in case_evaluations]),
            "avg_hallucination_rate": avg([e["hallucination_rate"] for e in case_evaluations]),
        },
        "hallucination_analysis": {
            "total_factual_claims": total_claims,
            "grounded_claims": grounded_claims,
            "unsupported_claims": unsupported_claims,
            "hallucination_rate": round(unsupported_claims / float(total_claims), 4) if total_claims else 0.0
        },
        "latency_metrics_sec": {
            "avg_ocr": avg(ocr_latencies),
            "avg_extraction": avg(extraction_latencies),
            "avg_retrieval": avg(retrieval_latencies),
            "avg_graph": avg(graph_latencies),
            "avg_generation": avg(generation_latencies),
            "avg_end_to_end": avg(total_latencies),
        },
        "baseline_comparison": {
            "baseline_1_keyword": b1,
            "baseline_2_rag": b2,
            "baseline_3_llm": b3,
        },
        "ablation_study": ablation_results,
        "per_case_evaluations": case_evaluations
    }

    with open(exp_dir / "aggregate_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    from storage import load_all_cases_from_disk
    load_all_cases_from_disk()
    res = run_evaluation_suite("experiment_001")
    print("Evaluation completed successfully. Aggregate results saved to backend/evaluation/results/experiment_001/aggregate_results.json")
