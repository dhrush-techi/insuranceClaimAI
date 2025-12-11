# backend/pipeline/confidence_calibrator.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from .reasoning import ReasoningResult
from .evidence_accumulator import EvidenceAggregate
from .analyzer import DenialAnalysis
from . import pattern_miner

@dataclass
class CalibratedConfidence:
    calibrated_score: float
    bucket: str  # HIGH / MEDIUM / LOW
    recommended_action: str  # AUTO_DRAFT / NEEDS_REVIEW / INCOMPLETE_EVIDENCE
    policy_flags: Dict[str, Any]

def calibrate_confidence(
    reasoning: ReasoningResult,
    evidence_agg: EvidenceAggregate,
    analysis: DenialAnalysis,
) -> CalibratedConfidence:
    score = reasoning.confidence_score

    # Use historical patterns (if any)
    stats = pattern_miner.get_category_stats(analysis.denial_category)
    if stats:
        avg = stats.get("avg_score", 60.0)
        if avg < 50:
            score -= 5.0
        elif avg > 75:
            score += 3.0

    # Penalize if evidence is extremely sparse
    if evidence_agg.total_items < 2:
        score -= 10.0

    # Policy guardrails
    policy_flags: Dict[str, Any] = {}
    if "experimental" in (analysis.denial_reason_raw or "").lower():
        # This type often needs careful legal framing – push to review
        policy_flags["experimental_treatment"] = True
        score = min(score, 70.0)

    score = max(0.0, min(100.0, score))

    if score >= 80:
        bucket = "HIGH"
        action = "AUTO_DRAFT"
    elif score >= 55:
        bucket = "MEDIUM"
        action = "NEEDS_REVIEW"
    else:
        bucket = "LOW"
        action = "INCOMPLETE_EVIDENCE"

    # If original reasoning already said INCOMPLETE_EVIDENCE, keep that
    if reasoning.decision == "INCOMPLETE_EVIDENCE":
        action = "INCOMPLETE_EVIDENCE"

    return CalibratedConfidence(
        calibrated_score=score,
        bucket=bucket,
        recommended_action=action,
        policy_flags=policy_flags,
    )

def to_json(cc: CalibratedConfidence) -> Dict[str, Any]:
    return {
        "calibrated_score": cc.calibrated_score,
        "bucket": cc.bucket,
        "recommended_action": cc.recommended_action,
        "policy_flags": cc.policy_flags,
    }
