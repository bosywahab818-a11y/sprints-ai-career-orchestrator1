# Sprints AI Career Orchestrator

## Overview

A multi-agent AI prototype built using LangGraph to support
learners throughout their training and career journey.

The system integrates three components into one unified
LangGraph StateGraph.

## 1. Curriculum Advisor

- Retrieval-Augmented Generation (RAG)
- ChromaDB vector retrieval
- Sentence-transformer embeddings
- Evidence-aware responses
- Unsupported-question rejection

## 2. Python Assessor

- Python submission validation
- Hosted E2B sandbox execution
- Automated test-based grading
- Feedback evaluation and optimization
- SQLite assessment persistence

## 3. Career Matching Agent

- SQLite learner and job retrieval
- Deterministic eligibility checks
- Explainable match scoring
- Human-in-the-loop approval using LangGraph interrupts
- Eligibility revalidation before approval

## Architecture

Unified LangGraph StateGraph
    |
    +-- Curriculum Advisor
    |
    +-- Python Assessor
    |       |
    |       +-- E2B sandbox
    |       +-- SQLite grade persistence
    |
    +-- Career Matching
            |
            +-- SQLite records
            +-- Human approval interrupt

## Data

The current demonstration uses:
- A sample curriculum
- A learner dataset containing 25 records
- Synthetic job openings

Synthetic job openings are not verified live vacancies.

## Setup

1. Clone the repository in Google Colab.
2. Install dependencies with `pip install -r requirements.txt`.
3. Configure `E2B_API_KEY` securely for sandbox execution.
4. Open `Sprints_AI_Career_Orchestrator_Demo.ipynb`.
5. Run the setup and demonstration cells in order.

The project includes a local SQLite demonstration database.
The Advisor also requires its sample curriculum index to be
initialized or made available.

A complete clean-runtime execution remains to be verified.

## Testing

Run the automated regression tests:

```bash
python -m pytest tests/test_core.py -v
```

Verified automated results: **12 passed**.

These tests cover:
- SQLite database integrity
- Learner and demonstration job records
- Learner profile retrieval
- Career matching and match verification
- Advisor, Assessor, Career and invalid-task routing
- Approval decision schema validation

Separately verified manual integration demonstrations:
- Advisor answer generation and unsupported-question rejection
- E2B Python execution and grading
- Unified Assessor-to-SQLite persistence
- Career human-approval interrupt and resume
- Valid approval, explicit rejection and invalid-decision rejection

Sandbox timeout handling, duplicate prevention, and learner
session isolation are not claimed as covered by the current
12-test regression suite.

## Demonstration Notebook

`Sprints_AI_Career_Orchestrator_Demo.ipynb`

This notebook contains 18 cells, including 8 Python code cells.

The original development notebook is retained separately.
The clean demonstration notebook has passed structural and
syntax validation, but has not yet passed a fresh-runtime
execution test.

## Current Limitations

- MemorySaver checkpoints are not durable across runtime restarts.
- The notebook uses simulated reviewer identities.
- Career openings are synthetic demonstration records.
- The curriculum is sample content.
- The system requires further production security hardening.
- A clean-runtime reproducibility test is still required.

## Final Demonstration

The final learner journey report is stored at:

docs/final_demo_report.json
