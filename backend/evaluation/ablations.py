# backend/evaluation/ablations.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from pipeline.ocr import DocumentIngestionResult, ingest_document
from pipeline.analyzer import analyze_denial_text
from pipeline.investigator import extract_evidence
from pipeline.evidence_accumulator import accumulate_evidence
from pipeline.traceability import build_traceability_graph
from pipeline.confidence_calibrator import calibrate_confidence
from pipeline.reasoning import reason_about_case
from pipeline.adaptive_template import select_template
from pipeline.advocate import generate_letter

@dataclass
class AblationConfig:
    ablation_id: str
    name: str
    use_span_indexing: bool = True
    use_akg_graph: bool = True
    use_confidence_calibration: bool = True
    use_semantic_retrieval: bool = True
    use_guardrails: bool = True

ABLATION_SUITE = {
    "A": AblationConfig("A", "Complete Proposed System"),
    "B": AblationConfig("B", "Without Span-Indexed Evidence", use_span_indexing=False),
    "C": AblationConfig("C", "Without Appeal Knowledge Graph (AKG)", use_akg_graph=False),
    "D": AblationConfig("D", "Without Confidence Calibration", use_confidence_calibration=False),
    "E": AblationConfig("E", "Without Semantic Retrieval", use_semantic_retrieval=False),
    "F": AblationConfig("F", "Without Guardrails/Evidence Constraints", use_guardrails=False),
}

def run_ablation_experiment(
    config: AblationConfig,
    denial_text: str,
    medical_text: str,
    case_id: str = "ablation_case_001"
) -> Dict[str, Any]:
    analysis = analyze_denial_text(denial_text)

    # Phase 3: Investigator
    if config.use_semantic_retrieval:
        evidence_bundle = extract_evidence(medical_text, analysis.denial_category, analysis.denial_reason_raw)
    else:
        # Dummy fallback non-semantic items
        evidence_bundle = extract_evidence("", analysis.denial_category, analysis.denial_reason_raw)

    # Strip spans if B is active
    if not config.use_span_indexing:
        for item in evidence_bundle.evidence_items:
            item.start_char = -1
            item.end_char = -1

    # Phase 4: Evidence Accumulator
    evidence_agg = accumulate_evidence(evidence_bundle)

    # Phase 5: AKG
    trace_graph = None
    if config.use_akg_graph:
        trace_graph = build_traceability_graph(case_id, analysis, evidence_bundle)

    # Phase 7: Reasoning Engine
    reasoning = reason_about_case(analysis.denial_category, analysis.denial_reason_raw, evidence_agg)

    # Phase 6: Confidence Calibration
    if config.use_confidence_calibration:
        calibrated = calibrate_confidence(reasoning, evidence_agg, analysis)
    else:
        # Default fixed calibrated result
        calibrated = calibrate_confidence(reasoning, evidence_agg, analysis, threshold=0.0)

    # Phase 8 & 9: Template & Advocate
    template_sel = select_template(analysis.denial_category, calibrated)
    letter = generate_letter(
        template_id=template_sel.template_id,
        denial_category=analysis.denial_category,
        denial_reason=analysis.denial_reason_raw,
        insurer_name=analysis.insurer_name,
        evidence_snippets=evidence_bundle.summary,
        reasoning_summary=reasoning.reasoning_summary,
        evidence_items=[asdict(e) for e in evidence_bundle.evidence_items] if config.use_guardrails else None,
    )

    return {
        "ablation_id": config.ablation_id,
        "name": config.name,
        "config": asdict(config),
        "evidence_count": len(evidence_bundle.evidence_items),
        "coverage_depth": evidence_agg.coverage_depth,
        "calibrated_score": calibrated.calibrated_score,
        "recommended_action": calibrated.recommended_action,
        "has_akg_graph": trace_graph is not None,
        "letter_text": letter.letter_text,
    }
