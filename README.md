# Lighthouse AI — Glass-Box Evidence-Grounded Medical Insurance Appeal System

This repository implements the production backend, multi-agent AI pipeline, research evaluation framework, and baseline/ablation experimental suite for:

> **"A Glass-Box, Evidence-Grounded AI System for Eliminating Inefficiency and Black-Box Uncertainty in Medical Insurance Appeal Generation"** (Patent Form 2 Specification)

---

## Architectural Workflow (10 Patent-Aligned Phases)

1. **Phase 1: Ingestion & Normalization (`backend/pipeline/ocr.py`)**
   - Ingests PDF, DOCX, and scanned image documents.
   - Tracks page numbers, character start/end bounds, and computes dictionary word quality $Q_{ocr}$.

2. **Phase 2: Analyzer Agent (`backend/pipeline/analyzer.py`)**
   - Extracts Insurer Name, Claim Adjustment Reason Codes (CARC), Denial Category, and Verbatim Denial Reasoning ($N_d$).

3. **Phase 3: Investigator Agent (`backend/pipeline/investigator.py`)**
   - Dense vector + TF-IDF hybrid semantic retrieval over medical records.
   - Preserves exact character start (`start_char`) and end (`end_char`) coordinates and source document ID.

4. **Phase 4: Evidence Accumulator (`backend/pipeline/evidence_accumulator.py`)**
   - Deduplicates evidence, sorts chronologically, and calculates Patent-Aligned Coverage Depth Metric:
     $$C_{depth} = \min\left(1.0, \frac{\sum \text{score}_i \cdot \text{weight}(\text{type}_i)}{0.85}\right)$$

5. **Phase 5: Traceability Engine / AKG (`backend/pipeline/traceability.py`)**
   - Builds per-case Appeal Knowledge Graph (Directed Acyclic Graph) linking Denial Premise ($N_d$), Evidence Facts ($N_e$), and Policy Rules ($N_p$) via `REFUTES` and `SUPPORTS` edges.

6. **Phase 6: Confidence Calibration (`backend/pipeline/confidence_calibrator.py`)**
   - Calculates quantitative viability score:
     $$S_{total} = w_{ocr} \cdot Q_{ocr} + w_{coverage} \cdot C_{depth} + w_{consistency} \cdot L_{consistency}$$
   - Routes case to `AUTO_DRAFT` if $S_{total} \ge 0.70$, else `MANUAL_REVIEW`.

7. **Phase 7: Reasoning Engine (`backend/pipeline/reasoning.py`)**
   - Chain-of-Thought (CoT) symbolic refutation comparing denial premise $N_d$ against evidence facts $N_e$.

8. **Phase 8: Adaptive Template Selector (`backend/pipeline/adaptive_template.py`)**
   - Dynamically selects optimal appeal structure based on insurer, category, and state regulations.

9. **Phase 9: Advocate Agent (`backend/pipeline/advocate.py`)**
   - Constrained appeal text generation with inline span citations `[Evidence EV-XXX (Doc, Page, Spans)]` and non-hallucination guardrails.

10. **Phase 10: RAG Chatbot (`backend/pipeline/chatbot.py`)**
    - Case-specific interactive chatbot providing evidence-backed answers with clickable span coordinates.

---

## Quickstart & Setup

### 1. Requirements & Dependencies
Ensure Python 3.10+ is installed.

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in `backend/`:
```env
PORT=8000
ENVIRONMENT=development
ROUTING_THRESHOLD=0.70
```

### 3. Launch Backend API
```bash
uvicorn app:app --reload --port 8000
```

---

## Reproducing Research Experiments

### Run Complete Benchmark Evaluation
To execute the empirical evaluation suite across all cases, compute latency breakdowns, run 3 baselines, and execute all 6 ablations:

```bash
python -m backend.evaluation.runner
```

Results will be automatically written to:
`backend/evaluation/results/experiment_001/aggregate_results.json`

### View Standalone Research Dashboard
Open `research_results/index.html` in any browser to inspect the interactive evaluation metrics, latency charts, baseline comparisons, and evidence span inspector.

---

## API Endpoints

- `POST /api/cases`: Initialize new case.
- `POST /api/cases/{case_id}/documents`: Upload denial letter and medical records for full processing.
- `GET /api/cases/{case_id}/evidence`: Retrieve span-indexed clinical evidence.
- `GET /api/cases/{case_id}/graph`: Retrieve Appeal Knowledge Graph (AKG) nodes and edges.
- `GET /api/cases/{case_id}/confidence`: Retrieve viability score breakdown.
- `POST /api/cases/{case_id}/chat`: Case RAG chatbot query.
- `POST /api/evaluation/run`: Execute research benchmark evaluation.
- `GET /api/evaluation/results`: Fetch empirical benchmark result JSON.
