# backend/evaluation_engine.py
from __future__ import annotations
from typing import Dict, Any, List
import statistics

from storage import list_all_cases
from pipeline.pattern_miner import get_global_metrics

# -------------------------------
# Helper utilities
# -------------------------------

def safe_mean(values: List[float]) -> float:
    return round(statistics.mean(values), 4) if values else 0.0

def safe_stdev(values: List[float]) -> float:
    return round(statistics.stdev(values), 4) if len(values) > 1 else 0.0

# -------------------------------
# Core Evaluation Engine
# -------------------------------

def evaluate_system() -> Dict[str, Any]:
    cases = list_all_cases()

    evaluation: Dict[str, Any] = {}
    evaluation["total_cases"] = len(cases)

    if not cases:
        evaluation["status"] = "NO_DATA"
        return evaluation

    # -------------------------------------------------
    # A. Reasoning & Decision Metrics
    # -------------------------------------------------

    confidences = []
    decisions = {"AUTO_DRAFT": 0, "NEEDS_REVIEW": 0, "INCOMPLETE_EVIDENCE": 0}
    category_scores: Dict[str, List[float]] = {}

    for c in cases:
        if c.confidence_score is not None:
            confidences.append(c.confidence_score)

        decision = (c.confidence_output or {}).get("recommended_action")
        if decision:
            decisions[decision] = decisions.get(decision, 0) + 1

        cat = c.denial_category or "Unknown"
        category_scores.setdefault(cat, [])
        if c.confidence_score:
            category_scores[cat].append(c.confidence_score)

    evaluation["decision_metrics"] = {
        "mean_confidence": safe_mean(confidences),
        "confidence_std": safe_stdev(confidences),
        "decision_distribution": decisions,
        "avg_confidence_by_category": {
            k: safe_mean(v) for k, v in category_scores.items()
        },
    }

    # -------------------------------------------------
    # B. Evidence Quality Metrics
    # -------------------------------------------------

    evidence_counts = []
    avg_ev_conf = []

    evidence_type_distribution: Dict[str, int] = {}

    for c in cases:
        inv = c.investigator_output or {}
        ev_items = inv.get("evidence_items", [])
        evidence_counts.append(len(ev_items))

        for e in ev_items:
            etype = e["evidence_type"]
            evidence_type_distribution[etype] = (
                evidence_type_distribution.get(etype, 0) + 1
            )
            avg_ev_conf.append(e.get("confidence", 0.0))

    evaluation["evidence_metrics"] = {
        "avg_evidence_per_case": safe_mean(evidence_counts),
        "max_evidence_per_case": max(evidence_counts) if evidence_counts else 0,
        "avg_evidence_confidence": safe_mean(avg_ev_conf),
        "evidence_type_distribution": evidence_type_distribution,
    }

    # -------------------------------------------------
    # C. Calibration Metrics (RAW vs CALIBRATED)
    # -------------------------------------------------

    raw_scores = []
    calibrated_scores = []
    deltas = []
    buckets = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for c in cases:
        r = (c.reasoning_output or {}).get("confidence_score")
        cal = (c.confidence_output or {}).get("calibrated_score")
        bucket = (c.confidence_output or {}).get("bucket")

        if r is not None and cal is not None:
            raw_scores.append(r)
            calibrated_scores.append(cal)
            deltas.append(cal - r)

        if bucket:
            buckets[bucket] = buckets.get(bucket, 0) + 1

    evaluation["calibration_metrics"] = {
        "mean_raw_score": safe_mean(raw_scores),
        "mean_calibrated_score": safe_mean(calibrated_scores),
        "mean_calibration_delta": safe_mean(deltas),
        "bucket_distribution": buckets,
    }

    # -------------------------------------------------
    # D. Explainability & Traceability Metrics
    # -------------------------------------------------

    trace_nodes = []
    trace_edges = []

    for c in cases:
        graph = c.trace_graph or {}
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        trace_nodes.append(len(nodes))
        trace_edges.append(len(edges))

    fully_traceable = sum(1 for x in trace_nodes if x >= 5)

    evaluation["explainability_metrics"] = {
        "avg_trace_nodes": safe_mean(trace_nodes),
        "avg_trace_edges": safe_mean(trace_edges),
        "fully_traceable_ratio": round(
            fully_traceable / len(cases), 3
        ),
    }

    # -------------------------------------------------
    # E. Improvement vs Old Baseline
    # -------------------------------------------------

    # Baseline assumptions (documented in paper)
    baseline = {
        "avg_confidence": 52.0,
        "explainability": 0.0,
        "adaptation": 0.0,
    }

    evaluation["improvement_metrics"] = {
        "confidence_gain_pct": round(
            evaluation["decision_metrics"]["mean_confidence"] - baseline["avg_confidence"], 2
        ),
        "explainability_gain": evaluation["explainability_metrics"]["fully_traceable_ratio"],
        "adaptation_enabled": True,
    }

    # -------------------------------------------------
    # F. Global Pattern Statistics
    # -------------------------------------------------

    evaluation["pattern_metrics"] = get_global_metrics()

    evaluation["status"] = "OK"
    return evaluation
