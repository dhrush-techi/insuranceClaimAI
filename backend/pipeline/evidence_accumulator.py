# backend/pipeline/evidence_accumulator.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from pipeline.investigator import EvidenceItem, EvidenceBundle

@dataclass
class AccumulatedEvidence:
    deduplicated_items: List[EvidenceItem]
    coverage_depth: float
    evidence_counts_by_type: Dict[str, int]
    summary: str

TYPE_WEIGHTS = {
    "FAILED_THERAPY": 0.35,
    "SEVERITY": 0.30,
    "RISK": 0.20,
    "CODING_PROOF": 0.10,
    "AUTH_REFERENCE": 0.10,
    "ADMIN_CONTEXT": 0.05,
}

def calculate_coverage_depth(items: List[EvidenceItem]) -> float:
    """
    Patent-Aligned Coverage Depth Metric Formula:
    C_depth = min(1.0, sum(score_i * weight(type_i)) / N_required)
    where N_required = 1.2
    """
    if not items:
        return 0.0

    total_weighted_score = 0.0
    seen_texts = set()

    for item in items:
        # Ignore near duplicate texts
        norm_text = item.text.lower().strip()
        if norm_text in seen_texts:
            continue
        seen_texts.add(norm_text)

        weight = TYPE_WEIGHTS.get(item.evidence_type, 0.10)
        total_weighted_score += item.score * weight

    target_threshold = 0.85
    coverage = min(1.0, total_weighted_score / target_threshold)
    return round(coverage, 4)

def accumulate_evidence(bundle: EvidenceBundle) -> AccumulatedEvidence:
    raw_items = bundle.evidence_items
    unique_items: List[EvidenceItem] = []
    seen_keys = set()

    for item in raw_items:
        # Deduplicate based on text snippet signature
        sig = re_sub_spaces(item.text.lower())
        if sig in seen_keys:
            continue
        seen_keys.add(sig)
        unique_items.append(item)

    counts: Dict[str, int] = {}
    for item in unique_items:
        counts[item.evidence_type] = counts.get(item.evidence_type, 0) + 1

    coverage_depth = calculate_coverage_depth(unique_items)
    summary = f"Accumulated {len(unique_items)} deduplicated evidence items. Coverage Depth: {coverage_depth:.2f}."

    return AccumulatedEvidence(
        deduplicated_items=unique_items,
        coverage_depth=coverage_depth,
        evidence_counts_by_type=counts,
        summary=summary,
    )

def re_sub_spaces(text: str) -> str:
    import re
    return re.sub(r"\s+", " ", text).strip()

def to_json(acc: AccumulatedEvidence) -> Dict[str, Any]:
    return {
        "deduplicated_items": [asdict(e) for e in acc.deduplicated_items],
        "coverage_depth": acc.coverage_depth,
        "evidence_counts_by_type": acc.evidence_counts_by_type,
        "summary": acc.summary,
    }
