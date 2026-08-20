# System Architecture Specification: Customer Support Resolution Desk

## 1. Executive Summary

The Customer Support Resolution Desk is an enterprise-grade automated triage and response system designed to process high volumes of inbound customer support tickets efficiently. By pairing **LangGraph** orchestration with **Gemini**, the system minimizes human intervention for routine inquiries while implementing strict structural guardrails, deterministic category enums, 3-way intent routing, and confidence thresholds to route complex edge cases to human specialists.

---

## 2. Core Architecture & Workflow State Machine

The system operates as a state-based directed acyclic graph (DAG) managed via LangGraph (`src/graph/workflow.py`). The lifecycle of an incoming customer support ticket follows these distinct phases:

```
                ┌───────────────────────────────┐
                │    INCOMING EMAIL WEBHOOK       │
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  Ingest Node                     │──► Extracts metadata, sender email,
                │                                   │    masks PII, and initializes state
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  Intent Classifier               │──► Gemini + Pydantic Enum Constraint
                └───────────────┬─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │ 3-Way Router  │               │
                ▼               ▼               ▼
        ┌───────────────┐┌───────────────┐┌───────────────┐
        │  Refund Agent ││Technical Agent││ General Agent │──► Department-specific RAG retrieval
        │ (DB & Policies││ (Troubleshoot)││ (Policy & FAQ)│    & live database tools
        └───────┬───────┘└───────┬───────┘└───────┬───────┘
                │                │                │
                └────────┬───────┴────────┬───────┘
                         │                │
                         ▼                ▼
                ┌───────────────────────────────┐
                │  Answer Composer               │──► Unified grounded draft generation
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  Confidence Gate               │──► Evaluates confidence score threshold
                └───────────────┬───────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
          [ Passed ]                       [ Failed ]
                │                               │
                ▼                               ▼
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │  Automated Response &     │    │  Handover Node             │
  │  End                       │    │  → Human Support Escalation│
  └─────────────────────────┘    └─────────────────────────┘
```

---

## 3. Detailed Component Breakdown

### A. Data Validation & Schemas
**Directory:** `src/schemas/`

- **`tickets.py`** — Enforces strict Pydantic models and Enums (`order_status`, `returns`, `subscriptions`, `other_complex`). This completely blocks free-text drift at the classification boundary.
- **`state.py`** — Defines `TicketResolutionState`, a unified state schema shared across all nodes containing raw text, metadata, classification results, retrieved docs, draft responses, and an immutable `audit_trail`.

### B. Specialized Agent Layer & Multi-Agent Branching
**Directory:** `src/agents/` & `src/graph/nodes.py`

- **`classifier.py`** — Houses the system prompt and routing logic for intent classification, binding Gemini to the `ClassificationResult` Pydantic schema with a temperature of 0.0.
- **Refund Agent Node** — Specialized branch equipped with vector retrieval and a live database tool (`MockDatabaseService`) to fetch real-time tracking numbers and shipping statuses for order inquiries.
- **Technical Agent Node** — Specialized branch dedicated to troubleshooting technical errors and subscription support queries via targeted RAG retrieval.
- **General Agent Node** — Specialized branch handling complex policies and general customer inquiries.
- **Answer Composer Node** — Unified generation module that compiles context chunks from whichever specialist agent ran to draft a precise, grounded response via `responder.py`.

### C. Orchestration & Workflow
**Directory:** `src/graph/`

- **`nodes.py`** — Contains modular node functions (`ingest_node`, `classify_node`, `refund_agent_node`, `technical_agent_node`, `general_agent_node`, `answer_composer_node`, `confidence_gate_node`, `handover_node`).
- **`workflow.py`** — Compiles the `StateGraph` with persistent SQLite checkpointers (`checkpoints.sqlite`), executing a 3-way conditional intent router after classification and routing low-confidence or escalated tickets to human handlers.

### D. Services & Core Utilities
**Directory:** `src/services/`

- **`config.py`** — Centralized configuration management handling API keys, model names, temperatures, and confidence thresholds.
- **`db.py`** — Simulates a live backend database service returning dynamic, relative delivery timestamps and tracking details.
- **`llm.py`** — Unified factory function providing reusable Gemini client instances with optional Pydantic structured output bindings.
- **`rag.py`** — Vector store retrieval module (ChromaDB) designed for targeted top-k chunking to minimize token usage.
- **`guardrails.py`** — Manages prompt injection detection, PII masking, token filtering, and auto-responder detection.

### E. API & Ingestion
**Directory:** `src/api/`

- **`main.py`** — FastAPI application factory exposing webhook endpoints (`/webhook/email`) to receive incoming customer support messages and execute the workflow synchronously.

---

## 4. Technical Guardrails & Data Governance

- **Structured Output Enforcement** — LLM outputs are programmatically constrained using Pydantic, ensuring type-safe processing down the graph pipeline.
- **Auditability** — Every node appends timestamped actions to the `audit_trail` list inside the workflow state for compliance and debugging.
- **Fail-Safe Escalation** — Any ticket flagged by security guardrails or scoring below the category confidence threshold is automatically routed to the human support queue.

---

## 5. Evaluation & Continuous Improvement

**Golden Dataset:** `tests/golden_dataset.json`

A curated set of labeled historical support tickets used to calculate classification accuracy, test multi-agent branch routing, track confusion matrices, and evaluate prompt changes before deployment.

## 🛡️ Enterprise Security & Observability Layer
1. **API Gateway & Rate Limiting**: Incoming webhooks pass through `slowapi` rate limiters and `X-API-Key` authentication headers before entering the LangGraph workflow.
2. **OpenTelemetry Tracing**: All agent node executions, tool lookups (`MockDatabaseService`, `MockSystemStatusService`), and state transitions are traced for telemetry auditing.

## 📊 Evaluation & Continuous Improvement Loop
* **LLM-as-a-Judge**: Evaluates completed ticket responses programmatically against the golden dataset (`tests/golden_dataset.json`).
* **Human-in-the-Loop (HITL) Feedback**: Operators can submit corrected responses via the Streamlit UI webhook (`/webhook/feedback`), dynamically updating golden records and few-shot routing examples.