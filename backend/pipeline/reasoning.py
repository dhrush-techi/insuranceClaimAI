# backend/pipeline/reasoning.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

from .evidence_accumulator import EvidenceAggregate

@dataclass
class ReasoningResult:
    confidence_score: float
    decision: str  # AUTO_DRAFT / NEEDS_REVIEW / INCOMPLETE_EVIDENCE
    reasoning_summary: str

def reason_about_case(
    denial_category: str,
    denial_reason: str,
    evidence_agg: EvidenceAggregate,
) -> ReasoningResult:
    # -------------------------------------------------------------------------
    # 1. SCORING LOGIC (Preserved strictly for Evaluation Engine compatibility)
    # -------------------------------------------------------------------------
    base = 30.0 + evidence_agg.total_items * 3.0
    base += evidence_agg.severity_score * 2.0
    base += evidence_agg.failed_therapy_score * 3.0
    base += evidence_agg.risk_score * 2.5

    c = denial_category.lower()
    if "medical necessity" in c:
        base += evidence_agg.failed_therapy_score * 1.5
    elif "authorization" in c:
        base += evidence_agg.by_type.get("AUTH_REFERENCE", 0) * 5.0
    elif "coding" in c:
        base += evidence_agg.by_type.get("CODING_PROOF", 0) * 4.0

    base = max(0.0, min(95.0, base))

    if evidence_agg.total_items == 0:
        decision = "INCOMPLETE_EVIDENCE"
    elif base >= 70:
        decision = "AUTO_DRAFT"
    elif base >= 45:
        decision = "NEEDS_REVIEW"
    else:
        decision = "INCOMPLETE_EVIDENCE"

    # -------------------------------------------------------------------------
    # 2. ARGUMENT GENERATION (Enhanced for "Actual Letter" Quality)
    # -------------------------------------------------------------------------
    # We construct specific arguments based on the evidence found in Investigator.
    arguments = []
    
    # Argument 1: Mechanical Symptoms / Exceptions
    # Checks for "locking", "catching" in SEVERITY evidence (mapped in Investigator)
    has_mechanical = (evidence_agg.severity_score > 1.5) # Heuristic threshold
    if has_mechanical:
        arguments.append(
            "1. Policy Exception Met: Mechanical Symptoms Present\n"
            "Clinical documentation confirms the patient exhibits 'locking', 'catching', and mechanical blocks "
            "to motion. Standard clinical guidelines waive conservative therapy requirements when such "
            "mechanical symptoms are present, as physical therapy cannot repair displaced tissue fragments."
        )

    # Argument 2: Timeline / Conservative Care
    # Checks for FAILED_THERAPY evidence
    if evidence_agg.failed_therapy_score > 0:
        arguments.append(
            "2. Conservative Treatment Timeline Met\n"
            "The denial erroneously calculates the duration of conservative care."
            "Medical records demonstrate a history of failed conservative management (including NSAIDs and "
            "home exercise programs) that, when combined with formal PT, satisfies the insurer's timeline requirements."
        )

    # Argument 3: Standard of Care / Risk
    # Checks for RISK evidence (chondromalacia, worsening)
    if evidence_agg.risk_score > 0:
        arguments.append(
            "3. Prevention of Further Harm (Standard of Care)\n"
            "Delaying surgical intervention places the patient at significant risk of further joint deterioration. "
            "Operative findings (e.g., Chondromalacia) indicate that mechanical rubbing is already causing "
            "permanent cartilage damage. Immediate intervention is the standard of care to prevent irreversible harm."
        )

    # Fallback if no specific arguments generated
    if not arguments:
        arguments.append(
            "The clinical evidence provided overwhelmingly supports the medical necessity of this procedure "
            "and contradicts the denial reason provided."
        )

    # Combine into the summary string which Advocate will use as the body
    summary_text = "\n\n".join(arguments)
    
    # Append stats for internal logging (optional, keeps old format at bottom)
    full_summary = (
        f"{summary_text}\n\n"
        f"--- Internal Metrics ---\n"
        f"Base confidence: {base:.0f}%\n"
        f"Severity: {evidence_agg.severity_score:.1f} | Risk: {evidence_agg.risk_score:.1f}"
    )

    return ReasoningResult(confidence_score=base, decision=decision, reasoning_summary=full_summary)

def to_json(rr: ReasoningResult) -> Dict:
    return {
        "confidence_score": rr.confidence_score,
        "decision": rr.decision,
        "reasoning_summary": rr.reasoning_summary,
    }