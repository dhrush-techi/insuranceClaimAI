# backend/pipeline/evidence_accumulator.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any

from .investigator import EvidenceBundle, EvidenceItem

@dataclass
class EvidenceAggregate:
    total_items: int
    by_type: Dict[str, int]
    avg_confidence: float
    severity_score: float
    failed_therapy_score: float
    risk_score: float

def accumulate_evidence(bundle: EvidenceBundle) -> EvidenceAggregate:
    items = bundle.evidence_items
    if not items:
        return EvidenceAggregate(
            total_items=0,
            by_type={},
            avg_confidence=0.0,
            severity_score=0.0,
            failed_therapy_score=0.0,
            risk_score=0.0,
        )

    by_type: Dict[str, int] = {}
    total_conf = 0.0
    severity_score = 0.0
    failed_score = 0.0
    risk_score = 0.0

    for e in items:
        by_type[e.evidence_type] = by_type.get(e.evidence_type, 0) + 1
        total_conf += e.confidence
        if e.evidence_type == "SEVERITY":
            severity_score += 1.0 * e.confidence
        elif e.evidence_type == "FAILED_THERAPY":
            failed_score += 1.2 * e.confidence
        elif e.evidence_type == "RISK":
            risk_score += 1.1 * e.confidence

    n = len(items)
    avg_conf = total_conf / n if n else 0.0
    return EvidenceAggregate(
        total_items=n,
        by_type=by_type,
        avg_confidence=avg_conf,
        severity_score=severity_score,
        failed_therapy_score=failed_score,
        risk_score=risk_score,
    )

def to_json(agg: EvidenceAggregate) -> Dict[str, Any]:
    return asdict(agg)
