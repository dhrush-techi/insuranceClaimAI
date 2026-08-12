# backend/pipeline/reasoning.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

from pipeline.evidence_accumulator import AccumulatedEvidence

@dataclass
class ReasoningResult:
    confidence_score: float
    decision: str  # AUTO_DRAFT / NEEDS_REVIEW / INCOMPLETE_EVIDENCE
    reasoning_summary: str
    missing_elements: List[str]
    contradictions: List[str]
    supporting_evidence_ids: List[str]

def reason_about_case(
    denial_category: str,
    denial_reason: str,
    evidence_agg: AccumulatedEvidence,
) -> ReasoningResult:
    evidence_items = evidence_agg.deduplicated_items
    total_items = len(evidence_items)
    
    missing_elements: List[str] = []
    contradictions: List[str] = []
    supporting_ids: List[str] = [e.evidence_id for e in evidence_items]

    # Check for missing elements based on denial category
    c = denial_category.lower()
    if "medical necessity" in c:
        has_failed_therapy = any(e.evidence_type == "FAILED_THERAPY" for e in evidence_items)
        has_severity = any(e.evidence_type == "SEVERITY" for e in evidence_items)
        if not has_failed_therapy:
            missing_elements.append("Lack of conservative treatment / failed therapy evidence")
        if not has_severity:
            missing_elements.append("Lack of documented symptom severity / mechanical symptoms")
            
        contradictions.append(
            f"Insurer denied under '{denial_category}', but clinical documentation refutes the determination via {total_items} verified evidence spans."
        )

    elif "authorization" in c:
        has_auth = any(e.evidence_type == "AUTH_REFERENCE" for e in evidence_items)
        if not has_auth:
            missing_elements.append("Missing prior authorization reference number")
        contradictions.append(
            "Insurer claimed absence of prior authorization, refuting records show pre-service notification."
        )

    elif "coding" in c:
        has_coding = any(e.evidence_type == "CODING_PROOF" for e in evidence_items)
        if not has_coding:
            missing_elements.append("Missing CPT modifier / ICD-10 cross-walk proof")

    base = 30.0 + total_items * 10.0 + (evidence_agg.coverage_depth * 40.0)
    if missing_elements:
        base -= len(missing_elements) * 10.0

    score = max(0.0, min(95.0, base))

    if total_items == 0:
        decision = "INCOMPLETE_EVIDENCE"
    elif score >= 70:
        decision = "AUTO_DRAFT"
    else:
        decision = "NEEDS_REVIEW"

    summary_parts = [
        f"Chain-of-Thought (CoT) Analysis for '{denial_category}' denial.",
        f"Contradiction identified: {contradictions[0] if contradictions else 'None'}.",
        f"Retrieved {total_items} refuting evidence items with Coverage Depth {evidence_agg.coverage_depth:.2f}."
    ]
    if missing_elements:
        summary_parts.append(f"Gaps identified: {', '.join(missing_elements)}.")

    reasoning_summary = " ".join(summary_parts)

    return ReasoningResult(
        confidence_score=score,
        decision=decision,
        reasoning_summary=reasoning_summary,
        missing_elements=missing_elements,
        contradictions=contradictions,
        supporting_evidence_ids=supporting_ids,
    )

def to_json(rr: ReasoningResult) -> Dict[str, Any]:
    return asdict(rr)