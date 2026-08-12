# backend/pipeline/analyzer.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
import re

@dataclass
class ExtractedEntity:
    entity_type: str
    text: str
    confidence: float
    start_char: int
    end_char: int

@dataclass
class DenialAnalysis:
    denial_reason_raw: str
    denial_category: str
    insurer_name: Optional[str]
    denial_code: Optional[str]
    category_scores: Dict[str, float]
    entities: List[ExtractedEntity]

CATEGORIES = {
    "medical necessity": "Medical Necessity",
    "not medically necessary": "Medical Necessity",
    "experimental": "Medical Necessity",
    "investigational": "Medical Necessity",
    "prior authorization": "Prior Authorization",
    "pre authorization": "Prior Authorization",
    "pre-authorization": "Prior Authorization",
    "precertification": "Prior Authorization",
    "coding": "Coding Error",
    "icd": "Coding Error",
    "cpt": "Coding Error",
    "modifier": "Coding Error",
    "unbundled": "Coding Error",
    "administrative": "Administrative",
    "late filing": "Administrative",
    "timely filing": "Administrative",
    "documentation missing": "Administrative",
    "out of network": "Administrative",
}

INSURER_PATTERNS = [
    r"(UnitedHealthcare|UHC|Optum)",
    r"(Blue\s+Cross\s+Blue\s+Shield|BCBS|Anthem)",
    r"(Aetna|Cigna|Humana|Kaiser\s+Permanente|Centene|Molina)",
    r"([A-Z][A-Za-z0-9\s]+(?:Insurance|Health\s+Plan|Healthcare|Mutual|Medical))"
]

CARC_PATTERNS = [
    r"\b(CO|PR|OA|PI|CR)[-\s]?(\d{1,4})\b",
    r"\bCARC[-\s]?(\d{1,4})\b",
    r"\b(CPT|ICD[-\d]*)[-\s]?(\d{4,5}|[A-Z0-9]{3,7})\b"
]

def analyze_denial_text(text: str) -> DenialAnalysis:
    if not text:
        return DenialAnalysis(
            denial_reason_raw="Empty document provided.",
            denial_category="Administrative",
            insurer_name=None,
            denial_code=None,
            category_scores={"Administrative": 1.0},
            entities=[]
        )

    lower = text.lower()
    scores: Dict[str, float] = {
        "Medical Necessity": 0.0,
        "Prior Authorization": 0.0,
        "Coding Error": 0.0,
        "Administrative": 0.0,
    }

    for key, category in CATEGORIES.items():
        matches = len(re.findall(r"\b" + re.escape(key) + r"\b", lower))
        scores[category] += matches * 1.5

    # Heuristics for direct matches
    if "not medically necessary" in lower or "experimental" in lower or "lack of clinical rationale" in lower:
        scores["Medical Necessity"] += 5.0
    if "prior authorization" in lower or "pre-auth" in lower:
        scores["Prior Authorization"] += 5.0
    if "cpt" in lower or "coding" in lower or "modifier" in lower:
        scores["Coding Error"] += 4.0

    category = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else "Medical Necessity"

    entities: List[ExtractedEntity] = []
    
    # 1. Insurer extraction
    insurer_name = None
    for pat in INSURER_PATTERNS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            insurer_name = match.group(0).strip()
            entities.append(
                ExtractedEntity(
                    entity_type="INSURER",
                    text=insurer_name,
                    confidence=0.90,
                    start_char=match.start(),
                    end_char=match.end()
                )
            )
            break
    if not insurer_name:
        insurer_name = _extract_insurer_fallback(text)

    # 2. Denial Code extraction (CARC/CPT)
    denial_code = None
    for pat in CARC_PATTERNS:
        match = re.search(pat, text)
        if match:
            denial_code = match.group(0).strip()
            entities.append(
                ExtractedEntity(
                    entity_type="DENIAL_CODE",
                    text=denial_code,
                    confidence=0.95,
                    start_char=match.start(),
                    end_char=match.end()
                )
            )
            break

    # 3. Verbatim Denial Reasoning
    denial_reason_raw = _extract_reason_snippet(text)
    if denial_reason_raw:
        reason_start = text.find(denial_reason_raw[:40]) if len(denial_reason_raw) >= 40 else 0
        entities.append(
            ExtractedEntity(
                entity_type="VERBATIM_REASONING",
                text=denial_reason_raw,
                confidence=0.88,
                start_char=max(0, reason_start),
                end_char=max(0, reason_start + len(denial_reason_raw))
            )
        )

    return DenialAnalysis(
        denial_reason_raw=denial_reason_raw,
        denial_category=category,
        insurer_name=insurer_name,
        denial_code=denial_code,
        category_scores=scores,
        entities=entities
    )

def _extract_insurer_fallback(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()][:10]
    for line in lines:
        if any(k in line.lower() for k in ["insurance", "health", "plan", "blue", "aetna", "cigna", "united"]):
            return line
    return "Health Insurance Plan"

def _extract_reason_snippet(text: str) -> str:
    lines = text.splitlines()
    capture = False
    buffer = []

    for line in lines:
        l_low = line.lower()
        if any(k in l_low for k in ["reason for denial", "denial reason", "basis for determination", "rationale:"]):
            capture = True
            continue
        if capture:
            if not line.strip() and len(buffer) > 0:
                break
            buffer.append(line.strip())

    if buffer:
        return " ".join(buffer)

    # Fallback search
    for line in lines:
        if any(k in line.lower() for k in ["denied", "not covered", "not authorized", "not medically necessary"]):
            return line.strip()

    return text[:300].strip() if text else "Claim denied based on plan determination."

def to_json(da: DenialAnalysis) -> Dict[str, Any]:
    return {
        "denial_reason_raw": da.denial_reason_raw,
        "denial_category": da.denial_category,
        "insurer_name": da.insurer_name,
        "denial_code": da.denial_code,
        "category_scores": da.category_scores,
        "entities": [asdict(e) for e in da.entities]
    }