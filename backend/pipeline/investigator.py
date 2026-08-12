# backend/pipeline/investigator.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Literal, Optional
import uuid
import re
import math

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
    document_id: str
    page: int
    text: str
    evidence_type: EvidenceType
    start_char: int
    end_char: int
    score: float
    confidence: float

@dataclass
class EvidenceBundle:
    evidence_items: List[EvidenceItem]
    summary: str

def _compute_tf_idf_similarity(query: str, text_chunk: str) -> float:
    def tokenize(s: str) -> List[str]:
        return [w for w in re.findall(r"\b\w{3,}\b", s.lower()) if w not in {"the", "and", "was", "for", "with", "that", "this"}]

    q_tokens = tokenize(query)
    c_tokens = tokenize(text_chunk)
    if not q_tokens or not c_tokens:
        return 0.0

    q_counts = {}
    for t in q_tokens:
        q_counts[t] = q_counts.get(t, 0) + 1

    c_counts = {}
    for t in c_tokens:
        c_counts[t] = c_counts.get(t, 0) + 1

    common = set(q_counts.keys()).intersection(c_counts.keys())
    if not common:
        return 0.0

    dot = sum(q_counts[t] * c_counts[t] for t in common)
    mag1 = math.sqrt(sum(v**2 for v in q_counts.values()))
    mag2 = math.sqrt(sum(v**2 for v in c_counts.values()))

    return dot / (mag1 * mag2)

def extract_evidence(
    medical_text: str,
    denial_category: str,
    denial_reason: str,
    document_id: str = "doc_medical_001",
    pages_data: Optional[List[Dict]] = None
) -> EvidenceBundle:
    if not medical_text or not medical_text.strip():
        return EvidenceBundle(evidence_items=[], summary="No medical text available for evidence discovery.")

    items: List[EvidenceItem] = []
    lines = medical_text.splitlines()
    offset = 0

    query_context = f"{denial_category} {denial_reason}"

    for idx, line in enumerate(lines):
        raw = line.strip()
        if not raw or len(raw) < 10:
            offset += len(line) + 1
            continue

        l = raw.lower()
        e_type: Optional[EvidenceType] = None
        base_conf = 0.40

        # Heuristic entity detection for clinical findings
        if any(k in l for k in ["failed", "ineffective", "refractory", "physical therapy", "nsaid", "conservative", "weeks of", "trial"]):
            e_type = "FAILED_THERAPY"
            base_conf = 0.78
            if any(char.isdigit() for char in l):
                base_conf = 0.88

        elif any(k in l for k in ["severe", "moderate", "pain", "worsening", "locking", "catching", "giving way", "tear", "block to motion", "swelling", "mri"]):
            e_type = "SEVERITY"
            base_conf = 0.82

        elif any(k in l for k in ["risk", "complication", "deterioration", "cartilage damage", "unstable", "urgent", "progression"]):
            e_type = "RISK"
            base_conf = 0.75

        elif any(k in l for k in ["cpt", "icd", "code", "procedure", "billed", "29881", "m23.222"]):
            e_type = "CODING_PROOF"
            base_conf = 0.70

        elif any(k in l for k in ["authorization", "pre-auth", "approval", "ref no", "reference"]):
            e_type = "AUTH_REFERENCE"
            base_conf = 0.70

        elif any(k in l for k in ["claim", "policy", "coverage", "deadline", "appeal"]):
            e_type = "ADMIN_CONTEXT"
            base_conf = 0.50

        if e_type:
            # Semantic similarity score
            sim_score = _compute_tf_idf_similarity(query_context, raw)
            combined_score = round(0.5 * base_conf + 0.5 * max(0.2, sim_score), 4)

            start_char = offset
            end_char = start_char + len(raw)

            # Determine page number
            page_num = 1
            if pages_data:
                for p in pages_data:
                    if p.get("char_start", 0) <= start_char <= p.get("char_end", 0):
                        page_num = p.get("page_number", 1)
                        break
            else:
                page_num = (idx // 35) + 1

            items.append(
                EvidenceItem(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    document_id=document_id,
                    page=page_num,
                    text=raw,
                    evidence_type=e_type,
                    start_char=start_char,
                    end_char=end_char,
                    score=combined_score,
                    confidence=base_conf,
                )
            )

        offset += len(line) + 1

    # Sort evidence items by combined relevance score
    items.sort(key=lambda x: x.score, reverse=True)

    if not items:
        summary = f"No span-indexed evidence retrieved for denial category '{denial_category}'."
    else:
        by_type: Dict[str, int] = {}
        for item in items:
            by_type[item.evidence_type] = by_type.get(item.evidence_type, 0) + 1
        type_str = ", ".join(f"{t}: {c}" for t, c in by_type.items())
        summary = f"Extracted {len(items)} span-indexed evidence items ({type_str})."

    return EvidenceBundle(evidence_items=items, summary=summary)

def to_json(bundle: EvidenceBundle) -> Dict:
    return {
        "evidence_items": [asdict(e) for e in bundle.evidence_items],
        "evidence_summary": bundle.summary,
    }