# backend/evaluation/baselines.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from pipeline.ocr import DocumentIngestionResult
from pipeline.analyzer import DenialAnalysis, analyze_denial_text
from pipeline.investigator import EvidenceBundle, EvidenceItem
from pipeline.evidence_accumulator import AccumulatedEvidence, accumulate_evidence
from pipeline.confidence_calibrator import CalibrationResult, calibrate_confidence
from pipeline.advocate import LetterDraft, generate_letter

def run_baseline_keyword(denial_text: str, medical_text: str) -> Dict[str, Any]:
    """Baseline 1: Keyword-based retrieval + template generation"""
    analysis = analyze_denial_text(denial_text)
    
    # Keyword search
    keywords = ["failed", "severe", "pain", "cpt", "authorization"]
    items = []
    lines = medical_text.splitlines()
    for idx, line in enumerate(lines):
        if any(k in line.lower() for k in keywords):
            items.append(
                EvidenceItem(
                    evidence_id=f"kw_{idx}",
                    document_id="doc_kw",
                    page=1,
                    text=line.strip(),
                    evidence_type="ADMIN_CONTEXT",
                    start_char=0,
                    end_char=len(line.strip()),
                    score=0.50,
                    confidence=0.50,
                )
            )
            
    bundle = EvidenceBundle(evidence_items=items, summary=f"Keyword retrieved {len(items)} snippets.")
    acc = accumulate_evidence(bundle)
    
    letter = generate_letter(
        template_id="standard",
        denial_category=analysis.denial_category,
        denial_reason=analysis.denial_reason_raw,
        insurer_name=analysis.insurer_name,
        evidence_snippets="\n".join([e.text for e in items]),
        reasoning_summary="Standard keyword-matched appeal.",
    )
    
    return {
        "baseline_name": "Keyword-Based Baseline",
        "analysis": asdict(analysis),
        "evidence_count": len(items),
        "coverage_depth": acc.coverage_depth,
        "letter_text": letter.letter_text,
    }

def run_baseline_rag(denial_text: str, medical_text: str) -> Dict[str, Any]:
    """Baseline 2: Basic semantic RAG without character span indexing or AKG"""
    analysis = analyze_denial_text(denial_text)
    
    # Simple semantic chunks
    chunks = [c.strip() for c in medical_text.split("\n\n") if len(c.strip()) > 20]
    items = []
    for idx, chunk in enumerate(chunks[:5]):
        items.append(
            EvidenceItem(
                evidence_id=f"rag_{idx}",
                document_id="doc_rag",
                page=1,
                text=chunk[:150],
                evidence_type="SEVERITY",
                start_char=-1,  # NO character span indexing in basic RAG
                end_char=-1,
                score=0.70,
                confidence=0.70,
            )
        )
        
    bundle = EvidenceBundle(evidence_items=items, summary=f"Basic RAG retrieved {len(items)} chunks.")
    
    letter = generate_letter(
        template_id="standard",
        denial_category=analysis.denial_category,
        denial_reason=analysis.denial_reason_raw,
        insurer_name=analysis.insurer_name,
        evidence_snippets="\n".join([e.text for e in items]),
        reasoning_summary="Basic RAG generated appeal without character-span citations.",
    )
    
    return {
        "baseline_name": "Basic Semantic RAG Baseline",
        "analysis": asdict(analysis),
        "evidence_count": len(items),
        "letter_text": letter.letter_text,
    }

def run_baseline_llm(denial_text: str, medical_text: str) -> Dict[str, Any]:
    """Baseline 3: Direct LLM generation without evidence retrieval pipeline"""
    analysis = analyze_denial_text(denial_text)
    
    unconstrained_letter = f"""RE: Appeal for Denied Claim ({analysis.denial_category})

To Insurer:
The patient underwent medically necessary procedures. Denial reason "{analysis.denial_reason_raw}" is incorrect.
Please approve this claim immediately.

Sincerely,
Physician
"""
    return {
        "baseline_name": "Generic LLM Baseline (Unconstrained)",
        "analysis": asdict(analysis),
        "evidence_count": 0,
        "letter_text": unconstrained_letter,
    }
