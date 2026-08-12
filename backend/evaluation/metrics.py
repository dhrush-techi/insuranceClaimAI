# backend/evaluation/metrics.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import statistics
import math

def calculate_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate (Levenshtein distance / reference length)"""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    
    r_len = len(reference)
    h_len = len(hypothesis)
    
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j
        
    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if reference[i-1] == hypothesis[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                
    return round(dp[r_len][h_len] / float(r_len), 4)

def calculate_wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate"""
    r_words = reference.strip().split()
    h_words = hypothesis.strip().split()
    
    if not r_words:
        return 0.0 if not h_words else 1.0
        
    r_len = len(r_words)
    h_len = len(h_words)
    
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j
        
    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if r_words[i-1] == h_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                
    return round(dp[r_len][h_len] / float(r_len), 4)

def calculate_ner_metrics(predicted_category: str, true_category: str) -> Tuple[float, float, float]:
    """Precision, Recall, F1 for categorical extraction"""
    match = 1.0 if predicted_category.lower() == true_category.lower() else 0.0
    return match, match, match

def calculate_retrieval_at_k(retrieved_spans: List[Dict], ground_truth_spans: List[Dict], k: int = 5) -> Dict[str, float]:
    """Precision@K, Recall@K, MRR"""
    top_k = retrieved_spans[:k]
    if not ground_truth_spans:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "mrr": 0.0}

    hits = 0
    first_hit_rank = 0

    for idx, item in enumerate(top_k, start=1):
        for gt in ground_truth_spans:
            # Overlap check
            if item.get("page") == gt.get("page") and abs(item.get("start_char", 0) - gt.get("start_char", 0)) < 100:
                hits += 1
                if first_hit_rank == 0:
                    first_hit_rank = idx
                break

    p_at_k = hits / float(k) if k > 0 else 0.0
    r_at_k = hits / float(len(ground_truth_spans)) if ground_truth_spans else 0.0
    mrr = 1.0 / first_hit_rank if first_hit_rank > 0 else 0.0

    return {
        "precision_at_k": round(p_at_k, 4),
        "recall_at_k": round(r_at_k, 4),
        "mrr": round(mrr, 4)
    }

def calculate_traceability_rate(evidence_items: List[Dict]) -> float:
    """Fraction of retrieved evidence items containing valid document_id, page, start_char, end_char"""
    if not evidence_items:
        return 0.0
    valid = 0
    for e in evidence_items:
        if e.get("document_id") and e.get("page") is not None and e.get("start_char") is not None and e.get("end_char") is not None:
            valid += 1
    return round(valid / float(len(evidence_items)), 4)

def calculate_grounding_and_hallucination(claims: List[str], evidence_items: List[Dict]) -> Tuple[float, float]:
    """
    Grounded rate: grounded claims / total factual claims
    Hallucination rate: unsupported claims / total factual claims
    """
    if not claims:
        return 1.0, 0.0

    ev_text_all = " ".join([e.get("text", "").lower() for e in evidence_items])
    grounded = 0
    unsupported = 0

    for c in claims:
        c_words = [w for w in c.lower().split() if len(w) > 3]
        if not c_words:
            grounded += 1
            continue
        matches = sum(1 for w in c_words if w in ev_text_all)
        if matches / float(len(c_words)) >= 0.35:
            grounded += 1
        else:
            unsupported += 1

    total = float(len(claims))
    return round(grounded / total, 4), round(unsupported / total, 4)
