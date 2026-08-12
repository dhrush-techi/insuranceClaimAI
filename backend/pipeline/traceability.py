# backend/pipeline/traceability.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pipeline.analyzer import DenialAnalysis
from pipeline.investigator import EvidenceBundle
from pipeline.reasoning import ReasoningResult

@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str  # "DENIAL_PREMISE" | "EVIDENCE_FACT" | "POLICY_RULE" | "APPEAL_CLAIM"
    properties: Dict[str, Any]

@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str  # "REFUTES" | "SUPPORTS" | "DERIVED_FROM"
    weight: float

@dataclass
class AppealKnowledgeGraph:
    case_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

def build_traceability_graph(
    case_id: str,
    analysis: DenialAnalysis,
    evidence_bundle: EvidenceBundle,
    reasoning: Optional[ReasoningResult] = None,
    letter: Optional[Any] = None,
) -> AppealKnowledgeGraph:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

    # 1. Denial Premise Node (N_d)
    denial_node_id = f"N_d_{case_id}"
    nodes.append(
        GraphNode(
            id=denial_node_id,
            label=f"Denial Premise: {analysis.denial_category}",
            node_type="DENIAL_PREMISE",
            properties={
                "category": analysis.denial_category,
                "reason_raw": analysis.denial_reason_raw,
                "insurer": analysis.insurer_name,
                "code": analysis.denial_code,
            },
        )
    )

    # 2. Evidence Fact Nodes (N_e)
    for idx, ev in enumerate(evidence_bundle.evidence_items[:15]):
        ev_node_id = f"N_e_{ev.evidence_id}"
        nodes.append(
            GraphNode(
                id=ev_node_id,
                label=f"Evidence: {ev.evidence_type}",
                node_type="EVIDENCE_FACT",
                properties={
                    "text": ev.text,
                    "document_id": ev.document_id,
                    "page": ev.page,
                    "start_char": ev.start_char,
                    "end_char": ev.end_char,
                    "score": ev.score,
                    "evidence_type": ev.evidence_type,
                },
            )
        )

        # Edge from Evidence to Denial Premise (REFUTES)
        rel = "REFUTES" if ev.evidence_type in ["FAILED_THERAPY", "SEVERITY", "RISK"] else "SUPPORTS"
        edges.append(
            GraphEdge(
                source=ev_node_id,
                target=denial_node_id,
                relation=rel,
                weight=ev.score,
            )
        )

    # 3. Policy / Clinical Guidelines Rule Node (N_p)
    policy_node_id = f"N_p_{case_id}"
    nodes.append(
        GraphNode(
            id=policy_node_id,
            label=f"Policy Rule: Standard of Care ({analysis.denial_category})",
            node_type="POLICY_RULE",
            properties={
                "description": f"Standard clinical guidelines for {analysis.denial_category}",
                "authority": "CMS / Medical Society Guidelines",
            },
        )
    )

    edges.append(
        GraphEdge(
            source=policy_node_id,
            target=denial_node_id,
            relation="REFUTES",
            weight=0.90,
        )
    )

    return AppealKnowledgeGraph(case_id=case_id, nodes=nodes, edges=edges)

def to_json(graph: AppealKnowledgeGraph) -> Dict[str, Any]:
    return {
        "case_id": graph.case_id,
        "nodes": [asdict(n) for n in graph.nodes],
        "edges": [asdict(e) for e in graph.edges],
    }
