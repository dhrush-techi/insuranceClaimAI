# backend/pipeline/chatbot.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pipeline.investigator import EvidenceItem
from pipeline.traceability import AppealKnowledgeGraph

@dataclass
class ChatResponse:
    answer: str
    citations: List[Dict[str, Any]]
    confidence_score: float

def answer_case_query(
    query: str,
    evidence_items: List[EvidenceItem],
    graph: Optional[AppealKnowledgeGraph] = None,
    denial_category: Optional[str] = None
) -> ChatResponse:
    if not query or not query.strip():
        return ChatResponse(
            answer="Please ask a specific question regarding the denial, medical records, or appeal strategy.",
            citations=[],
            confidence_score=0.0
        )

    q_lower = query.lower()
    matched_citations: List[Dict[str, Any]] = []
    
    # 1. Search evidence items matching user query
    matched_ev: List[EvidenceItem] = []
    for ev in evidence_items:
        t_low = ev.text.lower()
        if any(w in t_low for w in q_lower.split() if len(w) > 3):
            matched_ev.append(ev)

    if not matched_ev:
        matched_ev = evidence_items[:3]  # fallback to top evidence items

    for ev in matched_ev[:4]:
        matched_citations.append({
            "evidence_id": ev.evidence_id,
            "document_id": ev.document_id,
            "page": ev.page,
            "start_char": ev.start_char,
            "end_char": ev.end_char,
            "text": ev.text,
            "score": ev.score,
        })

    # 2. Synthesize answer with clickable citations
    if "evidence" in q_lower or "proof" in q_lower or "failed" in q_lower:
        snippets = "\n".join([f"- {c['text']} (Page {c['page']}, Spans {c['start_char']}-{c['end_char']})" for c in matched_citations])
        answer = f"Here is the relevant clinical evidence extracted from the medical records:\n\n{snippets}"
    elif "denial" in q_lower or "reason" in q_lower or "why" in q_lower:
        answer = f"The claim was denied under category '{denial_category or 'Medical Necessity'}'. Key refuting clinical evidence has been identified across {len(evidence_items)} document spans."
    elif "graph" in q_lower or "akg" in q_lower or "trace" in q_lower:
        num_nodes = len(graph.nodes) if graph else 0
        num_edges = len(graph.edges) if graph else 0
        answer = f"The Appeal Knowledge Graph (AKG) contains {num_nodes} nodes and {num_edges} directed edges linking the Denial Premise to refuting Evidence Facts."
    else:
        snippets = "\n".join([f"- {c['text']} [Doc: {c['document_id']}, Page: {c['page']}]" for c in matched_citations[:2]])
        answer = f"Based on the case records:\n{snippets}"

    return ChatResponse(
        answer=answer,
        citations=matched_citations,
        confidence_score=0.88 if matched_citations else 0.50
    )
