# backend/pipeline/analyzer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
import re

@dataclass
class DenialAnalysis:
    denial_reason_raw: str
    denial_category: str
    insurer_name: Optional[str]
    denial_code: Optional[str]
    category_scores: Dict[str, float]

CATEGORIES = {
    "medical necessity": "Medical Necessity",
    "not medically necessary": "Medical Necessity",
    "experimental": "Medical Necessity",
    "prior authorization": "Prior Authorization",
    "pre authorization": "Prior Authorization",
    "pre-authorization": "Prior Authorization",
    "coding": "Coding Error",
    "icd": "Coding Error",
    "cpt": "Coding Error",
    "modifier": "Coding Error",
    "administrative": "Administrative",
    "late filing": "Administrative",
    "timely filing": "Administrative",
    "documentation missing": "Administrative",
}

def analyze_denial_text(text: str) -> DenialAnalysis:
    lower = text.lower()
    scores: Dict[str, float] = {
        "Medical Necessity": 0.0,
        "Prior Authorization": 0.0,
        "Coding Error": 0.0,
        "Administrative": 0.0,
    }

    for key, category in CATEGORIES.items():
        if key in lower:
            scores[category] += 1.0

    # Default category logic
    category = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else "Administrative"
    
    # Heuristic: If "not medically necessary" is explicit, force category
    if "not medically necessary" in lower:
        category = "Medical Necessity"
        scores["Medical Necessity"] += 5.0

    insurer_name = _extract_insurer_name(text)
    denial_reason_raw = _extract_reason_snippet(text)
    denial_code = _extract_code(text)

    return DenialAnalysis(
        denial_reason_raw=denial_reason_raw,
        denial_category=category,
        insurer_name=insurer_name,
        denial_code=denial_code,
        category_scores=scores,
    )

def _extract_insurer_name(text: str) -> Optional[str]:
    # Look for lines that look like headers before we hit the body
    lines = text.splitlines()[:10]
    for line in lines:
        l = line.strip()
        if len(l) < 4: continue
        # Common insurance keywords
        if any(k in l.lower() for k in ["insurance", "health plan", "blue cross", "aetna", "cigna", "united", "humana", "medicare", "group"]):
            return l
    return "Health Insurance Plan"

def _extract_reason_snippet(text: str) -> str:
    # Try to find the paragraph specifically explaining the denial
    lines = text.splitlines()
    capture = False
    buffer = []
    
    for line in lines:
        l_low = line.lower()
        if any(k in l_low for k in ["reason for denial", "denial reason", "basis for determination"]):
            capture = True
            continue # Skip the header itself
        if capture:
            if len(line.strip()) == 0 and len(buffer) > 0:
                break # Stop at empty line after content
            buffer.append(line.strip())
            
    if buffer:
        return " ".join(buffer)

    # Fallback to searching for keywords
    for line in lines:
        if any(k in line.lower() for k in ["denied", "not covered", "not authorized"]):
            return line.strip()
            
    return "The claim was denied based on plan terms."

def _extract_code(text: str) -> Optional[str]:
    # Standard Claim Adjustment Reason Codes (CARC) patterns
    m = re.search(r"\b([A-Z]{2,3})[- ]?(\d{2,5})\b", text) # Matches CLM-99283 or CO-45
    if m:
        return m.group(0)
    return None

def to_json(da: DenialAnalysis) -> Dict:
    return {
        "denial_reason_raw": da.denial_reason_raw,
        "denial_category": da.denial_category,
        "insurer_name": da.insurer_name,
        "denial_code": da.denial_code,
        "category_scores": da.category_scores,
    }