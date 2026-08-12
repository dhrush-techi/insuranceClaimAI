# backend/evaluation/ground_truth_schema.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class GroundTruthSpan:
    document_id: str
    page: int
    start_char: int
    end_char: int
    expected_text: str
    evidence_type: str

@dataclass
class EvaluationTestCase:
    case_id: str
    denial_category: str
    denial_code: Optional[str]
    insurer_name: str
    verbatim_reasoning: str
    ground_truth_spans: List[GroundTruthSpan]
    expected_decision: str  # "AUTO_DRAFT" | "MANUAL_REVIEW"
    expected_relationships: List[Dict[str, str]]
    source_denial_file: Optional[str] = None
    source_medical_file: Optional[str] = None
    is_reference_annotation: bool = True  # Explicit tag: reference / auto-annotated vs human gold standard

def to_dict(gt_case: EvaluationTestCase) -> Dict[str, Any]:
    return asdict(gt_case)
