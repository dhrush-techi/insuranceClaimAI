# backend/pipeline/pattern_miner.py
from __future__ import annotations
from typing import Dict, Any
import json

from config import PATTERN_FILE
from .reasoning import ReasoningResult

def _load_patterns() -> Dict[str, Any]:
    if PATTERN_FILE.exists():
        with open(PATTERN_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save_patterns(data: Dict[str, Any]) -> None:
    with open(PATTERN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_patterns_on_case(
    denial_category: str,
    reasoning: ReasoningResult,
) -> None:
    data = _load_patterns()
    cat = denial_category or "Unknown"
    entry = data.get(cat, {"count": 0, "sum_score": 0.0})

    entry["count"] += 1
    entry["sum_score"] += float(reasoning.confidence_score)
    entry["avg_score"] = entry["sum_score"] / max(entry["count"], 1)
    data[cat] = entry
    _save_patterns(data)

def get_category_stats(denial_category: str) -> Dict[str, Any] | None:
    data = _load_patterns()
    return data.get(denial_category)

def get_global_metrics() -> Dict[str, Any]:
    data = _load_patterns()
    total_cases = sum(v.get("count", 0) for v in data.values())
    return {
        "total_cases_tracked": total_cases,
        "categories": data,
    }
