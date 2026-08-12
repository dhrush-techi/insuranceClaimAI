# backend/storage.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from config import CASE_DIR, FEEDBACK_FILE
import json

@dataclass
class CaseRecord:
    id: str
    user_id: str
    created_at: str

    denial_filename: Optional[str]
    medical_filename: Optional[str]

    denial_category: Optional[str]
    insurer_name: Optional[str]
    confidence_score: Optional[float]
    status: str  # processed / error / pending

    denial_reason_raw: Optional[str]
    reasoning_summary: Optional[str]
    evidence_summary: Optional[str]
    letter_text: Optional[str]

    # Raw texts
    denial_text: Optional[str]
    medical_text: Optional[str]

    # ---- Rich artifacts for traceability & evaluation ----
    analyzer_output: Optional[Dict[str, Any]] = None
    investigator_output: Optional[Dict[str, Any]] = None
    evidence_aggregate: Optional[Dict[str, Any]] = None
    reasoning_output: Optional[Dict[str, Any]] = None
    confidence_output: Optional[Dict[str, Any]] = None
    template_metadata: Optional[Dict[str, Any]] = None
    trace_graph: Optional[Dict[str, Any]] = None
    document_metadata: Optional[Dict[str, Any]] = None

# In-memory DB
_CASES: Dict[str, CaseRecord] = {}
_USER_CASE_IDS: Dict[str, List[str]] = {}

def save_case(case: CaseRecord) -> None:
    _CASES[case.id] = case
    if case.id not in _USER_CASE_IDS.get(case.user_id, []):
        _USER_CASE_IDS.setdefault(case.user_id, []).insert(0, case.id)
    path = CASE_DIR / f"{case.id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(case), f, ensure_ascii=False, indent=2)

def get_case_by_id(case_id: str) -> Optional[CaseRecord]:
    return _CASES.get(case_id)

def list_cases_for_user(user_id: str) -> List[CaseRecord]:
    ids = _USER_CASE_IDS.get(user_id, [])
    return [c for cid in ids if (c := _CASES.get(cid))]

def list_all_cases() -> List[CaseRecord]:
    return list(_CASES.values())

def load_all_cases_from_disk() -> None:
    for path in CASE_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            case = CaseRecord(
                id=data["id"],
                user_id=data["user_id"],
                created_at=data["created_at"],
                denial_filename=data.get("denial_filename"),
                medical_filename=data.get("medical_filename"),
                denial_category=data.get("denial_category"),
                insurer_name=data.get("insurer_name"),
                confidence_score=data.get("confidence_score"),
                status=data.get("status", "processed"),
                denial_reason_raw=data.get("denial_reason_raw"),
                reasoning_summary=data.get("reasoning_summary"),
                evidence_summary=data.get("evidence_summary"),
                letter_text=data.get("letter_text"),
                denial_text=data.get("denial_text"),
                medical_text=data.get("medical_text"),
                analyzer_output=data.get("analyzer_output"),
                investigator_output=data.get("investigator_output"),
                evidence_aggregate=data.get("evidence_aggregate"),
                reasoning_output=data.get("reasoning_output"),
                confidence_output=data.get("confidence_output"),
                template_metadata=data.get("template_metadata"),
                trace_graph=data.get("trace_graph"),
                document_metadata=data.get("document_metadata"),
            )
            _CASES[case.id] = case
            _USER_CASE_IDS.setdefault(case.user_id, []).append(case.id)
        except Exception:
            continue

# ---- Chat: per-case / per-user history ----

_CHAT_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

def append_chat(user_id: str, role: str, content: str) -> Dict[str, Any]:
    msg = {
        "id": f"msg_{datetime.utcnow().isoformat()}",
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _CHAT_HISTORY.setdefault(user_id, []).append(msg)
    return msg

def get_chat_history(user_id: str) -> List[Dict[str, Any]]:
    return _CHAT_HISTORY.get(user_id, [])

def append_feedback(entry: Dict[str, Any]) -> None:
    lines: List[str] = []
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    entry_with_time = {
        **entry,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    lines.append(json.dumps(entry_with_time))

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
