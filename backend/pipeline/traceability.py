# backend/pipeline/traceability.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from .investigator import EvidenceBundle
from .analyzer import DenialAnalysis
from .reasoning import ReasoningResult
from .advocate import LetterDraft

@dataclass
class GraphNode:
    id: str
    type: str
    label: str
    meta: Dict[str, Any]

@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str

@dataclass
class TraceabilityGraph:
    nodes: List[GraphNode]
    edges: List[GraphEdge]

def build_traceability_graph(
    case_id: str,
    denial: DenialAnalysis,
    evidence: EvidenceBundle,
    reasoning: ReasoningResult,
    letter: LetterDraft | None,
) -> TraceabilityGraph:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

    # Case node
    case_node_id = f"case:{case_id}"
    nodes.append(
        GraphNode(
            id=case_node_id,
            type="DenialCase",
            label=f"Case {case_id}",
            meta={
                "category": denial.denial_category,
                "insurer": denial.insurer_name,
                "denial_code": denial.denial_code,
            },
        )
    )

    # Reasoning node
    reasoning_id = f"reasoning:{case_id}"
    nodes.append(
        GraphNode(
            id=reasoning_id,
            type="ReasoningNode",
            label="Reasoning Engine",
            meta={
                "summary": reasoning.reasoning_summary,
                "confidence_score": reasoning.confidence_score,
                "decision": reasoning.decision,
            },
        )
    )
    edges.append(GraphEdge(source=case_node_id, target=reasoning_id, relation="EVALUATED_BY"))

    # Evidence nodes
    for e in evidence.evidence_items:
        ev_id = f"evidence:{e.evidence_id}"
        nodes.append(
            GraphNode(
                id=ev_id,
                type="EvidenceItem",
                label=e.evidence_type,
                meta={
                    "text": e.text,
                    "source": e.source,
                    "confidence": e.confidence,
                    "page_hint": e.page_hint,
                    "start_char": e.start_char,
                    "end_char": e.end_char,
                },
            )
        )
        edges.append(GraphEdge(source=ev_id, target=reasoning_id, relation="SUPPORTED_BY"))
        edges.append(GraphEdge(source=case_node_id, target=ev_id, relation="DENIED_FOR"))

    # Letter node
    if letter:
        letter_id = f"letter:{case_id}"
        nodes.append(
            GraphNode(
                id=letter_id,
                type="LetterDraft",
                label="Appeal Letter",
                meta={"preview": letter.letter_text[:300]},
            )
        )
        edges.append(GraphEdge(source=reasoning_id, target=letter_id, relation="GENERATED"))

    return TraceabilityGraph(nodes=nodes, edges=edges)

def to_json(graph: TraceabilityGraph) -> Dict[str, Any]:
    return {
        "nodes": [asdict(n) for n in graph.nodes],
        "edges": [asdict(e) for e in graph.edges],
    }
