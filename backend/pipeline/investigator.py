# backend/pipeline/investigator.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Literal
import uuid

EvidenceType = Literal[
    "FAILED_THERAPY",
    "SEVERITY",
    "RISK",
    "CODING_PROOF",
    "AUTH_REFERENCE",
    "ADMIN_CONTEXT",
]

@dataclass
class EvidenceItem:
    evidence_id: str
    source: str  # "medical" or "denial"
    text: str
    evidence_type: EvidenceType
    start_char: int
    end_char: int
    confidence: float
    page_hint: int | None = None

@dataclass
class EvidenceBundle:
    evidence_items: List[EvidenceItem]
    summary: str

def _scan_lines(text: str, category: str, denial_reason: str) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []
    lower_cat = category.lower()
    full_lower = text.lower()

    # Very rough page approximation
    lines = text.splitlines()
    offset = 0
    for idx, line in enumerate(lines):
        raw = line.strip()
        if not raw:
            offset += len(line) + 1
            continue

        l = raw.lower()
        e_type: EvidenceType | None = None
        conf = 0.4

        # EXPANDED HEURISTICS FOR ORTHOPEDIC/MEDICAL CONTEXT
        
        # 1. FAILED_THERAPY: Look for duration and specific conservative treatments
        if any(k in l for k in ["failed", "ineffective", "no response", "refractory", 
                                "physical therapy", "nsaid", "conservative", "weeks of"]):
            e_type = "FAILED_THERAPY"
            conf = 0.75
            # Boost confidence if specific timelines are mentioned
            if any(char.isdigit() for char in l):
                conf = 0.85

        # 2. SEVERITY: Expanded to include mechanical symptoms (Key for "Locked Knee" argument)
        elif any(k in l for k in ["severe", "moderate", "severely", "pain", "worsening", 
                                  "locking", "catching", "giving way", "mechanical", "unable to extend", 
                                  "block to motion", "tear", "complex tear", "bucket-handle"]):
            e_type = "SEVERITY"
            conf = 0.80 # Higher base confidence for specific symptoms

        # 3. RISK: Expanded to include standard of care and progression markers
        elif any(k in l for k in ["risk", "complication", "deterioration", "not treating", 
                                  "chondromalacia", "cartilage damage", "bone on bone", "flipping", 
                                  "unstable", "urgent"]):
            e_type = "RISK"
            conf = 0.75

        # 4. CODING_PROOF: Standard checks
        elif any(k in l for k in ["cpt", "icd", "code", "procedure", "billed", "29881", "m23.222"]):
            e_type = "CODING_PROOF"
            conf = 0.6

        # 5. AUTH_REFERENCE: Standard checks
        elif any(k in l for k in ["authorization", "pre-auth", "approval", "ref no"]):
            e_type = "AUTH_REFERENCE"
            conf = 0.6

        # 6. ADMIN_CONTEXT: Standard checks
        elif any(k in l for k in ["claim", "policy", "coverage", "deadline", "appeal"]):
            e_type = "ADMIN_CONTEXT"
            conf = 0.5

        if e_type:
            start_char = full_lower.find(l, offset)
            if start_char == -1:
                start_char = offset
            end_char = start_char + len(raw)
            page_hint = idx // 40  # rough

            items.append(
                EvidenceItem(
                    evidence_id=str(uuid.uuid4()),
                    source="medical",
                    text=raw,
                    evidence_type=e_type,
                    start_char=start_char,
                    end_char=end_char,
                    confidence=conf,
                    page_hint=page_hint,
                )
            )

        offset += len(line) + 1

    return items

def extract_evidence(medical_text: str, denial_category: str, denial_reason: str) -> EvidenceBundle:
    items = _scan_lines(medical_text, denial_category, denial_reason)
    if not items:
        summary = (
            f"No strong structured evidence could be extracted for category '{denial_category}'."
            f"Denial reason: {denial_reason[:200]}..."
        )
    else:
        by_type: Dict[str, int] = {}
        for item in items:
            by_type[item.evidence_type] = by_type.get(item.evidence_type, 0) + 1
        type_str = ", ".join(f"{t}: {c}" for t, c in by_type.items())
        summary = (
            f"Extracted {len(items)} evidence snippets for category '{denial_category}' "
            f"({type_str}). Denial reason: {denial_reason[:200]}..."
        )

    return EvidenceBundle(evidence_items=items, summary=summary)

def to_json(bundle: EvidenceBundle) -> Dict:
    return {
        "evidence_items": [asdict(e) for e in bundle.evidence_items],
        "evidence_summary": bundle.summary,
    }