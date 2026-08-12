# backend/pipeline/adaptive_template.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any

from pipeline.confidence_calibrator import CalibrationResult

@dataclass
class TemplateSelection:
    template_id: str
    tone: str  # "formal", "assertive"
    length: str  # "short", "standard", "detailed"

def select_template(
    denial_category: str,
    confidence: CalibrationResult,
) -> TemplateSelection:
    c = denial_category.lower()
    if "medical necessity" in c:
        template_id = "medical_necessity"
    elif "authorization" in c:
        template_id = "prior_auth"
    elif "coding" in c:
        template_id = "coding_error"
    else:
        template_id = "administrative"

    if confidence.bucket == "HIGH":
        tone = "assertive"
        length = "detailed"
    elif confidence.bucket == "MEDIUM":
        tone = "formal"
        length = "standard"
    else:
        tone = "formal"
        length = "short"

    return TemplateSelection(template_id=template_id, tone=tone, length=length)

def to_json(sel: TemplateSelection) -> Dict[str, Any]:
    return asdict(sel)