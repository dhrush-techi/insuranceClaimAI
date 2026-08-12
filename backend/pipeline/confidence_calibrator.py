# backend/pipeline/confidence_calibrator.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Literal
from pipeline.reasoning import ReasoningResult
from pipeline.evidence_accumulator import AccumulatedEvidence
from pipeline.analyzer import DenialAnalysis

DecisionType = Literal["AUTO_DRAFT", "MANUAL_REVIEW"]

@dataclass
class CalibrationResult:
    raw_reasoning_score: float
    ocr_quality: float
    coverage_depth: float
    logical_consistency: float
    calibrated_score: float
    recommended_action: DecisionType
    bucket: str
    breakdown: Dict[str, float]

# Expose weights and routing threshold as configuration
WEIGHT_OCR = 0.20
WEIGHT_COVERAGE = 0.50
WEIGHT_CONSISTENCY = 0.30
ROUTING_THRESHOLD = 0.70  # S_total >= 0.70 -> AUTO_DRAFT, else MANUAL_REVIEW

def calibrate_confidence(
    reasoning: ReasoningResult,
    evidence_agg: AccumulatedEvidence,
    analysis: DenialAnalysis,
    ocr_quality: float = 0.90,
    threshold: float = ROUTING_THRESHOLD,
) -> CalibrationResult:
    """
    Patent-Aligned Confidence Calibration Module Formula:
    S_total = w_ocr * Q_ocr + w_coverage * C_depth + w_consistency * L_consistency
    """
    q_ocr = max(0.0, min(1.0, ocr_quality))
    c_depth = max(0.0, min(1.0, evidence_agg.coverage_depth))
    
    # Measure logical consistency based on reasoning gaps and contradictions
    missing_gaps = len(reasoning.missing_elements or [])
    contradictions = len(reasoning.contradictions or [])
    
    l_consistency = 1.0 - (0.25 * missing_gaps + 0.35 * contradictions)
    l_consistency = max(0.10, min(1.0, l_consistency))

    s_total = (
        WEIGHT_OCR * q_ocr +
        WEIGHT_COVERAGE * c_depth +
        WEIGHT_CONSISTENCY * l_consistency
    )
    s_total = round(max(0.0, min(1.0, s_total)), 4)

    if s_total >= threshold:
        action: DecisionType = "AUTO_DRAFT"
    else:
        action: DecisionType = "MANUAL_REVIEW"

    if s_total >= 0.80:
        bucket = "HIGH"
    elif s_total >= 0.60:
        bucket = "MEDIUM"
    else:
        bucket = "LOW"

    breakdown = {
        "weighted_ocr": round(WEIGHT_OCR * q_ocr, 4),
        "weighted_coverage": round(WEIGHT_COVERAGE * c_depth, 4),
        "weighted_consistency": round(WEIGHT_CONSISTENCY * l_consistency, 4),
        "routing_threshold": threshold,
    }

    return CalibrationResult(
        raw_reasoning_score=reasoning.confidence_score,
        ocr_quality=q_ocr,
        coverage_depth=c_depth,
        logical_consistency=l_consistency,
        calibrated_score=s_total,
        recommended_action=action,
        bucket=bucket,
        breakdown=breakdown,
    )

def to_json(cr: CalibrationResult) -> Dict[str, Any]:
    return asdict(cr)
