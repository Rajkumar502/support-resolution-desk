# System Architecture Specification: Customer Support Resolution Desk

## 1. Executive Summary

The Customer Support Resolution Desk is an enterprise-grade automated triage and response system designed to process high volumes of inbound customer support tickets efficiently. By pairing **LangGraph** orchestration with **Gemini**, the system minimizes human intervention for routine inquiries while implementing strict structural guardrails, deterministic category enums, 3-way intent routing, security headers, and confidence thresholds to route complex edge cases or security threats to human specialists.

---

## 2. Core Architecture & Workflow State Machine

The system operates as a state-based directed acyclic graph (DAG) managed via LangGraph (`src/graph/workflow.py`). The lifecycle of an incoming customer support ticket follows these distinct phases:

```
            ┌──────────────────────────────────────┐
            │    FASTAPI WEBHOOK + X-API-KEY          │
            │    (Protected by slowapi Rate Limiter)  │
            └──────────────────┬───────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │  Ingest Node                            │──► Extracts metadata, sender email,
            │                                          │    masks PII, and initializes state
            └──────────────────┬───────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │  Intent Classifier                      │──► Gemini + Pydantic Enum Constraint
            └──────────────────┬───────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │ 3-Way Router     │                  │
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │  Refund Agent │  │Technical Agent│  │ General Agent │──► Department-specific RAG retrieval
    │ (DB & Policies│  │ (Troubleshoot)│  │ (Policy & FAQ)│    & live database tools
    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
            │                  │                  │
            └──────────┬───────┴──────────┬───────┘
                       │                  │
                       ▼                  ▼
            ┌──────────────────────────────────────┐
            │  Answer Composer                        │──► Unified grounded draft generation
            └──────────────────┬───────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │  Confidence Gate & Security             │──► Evaluates confidence & checks for
            │  Interceptor                             │    jailbreaks
            └──────────────────┬───────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
      [ Passed ]                             [ Failed ]
            │                                     │
            ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│  Automated Response &     │           │  Handover Node             │
│  End                       │           │  → Human Escalation Queue │
└─────────────────────────┘           └─────────────────────────┘
```

---

## 3. Detailed Component Breakdown

### A. Data Validation & Schemas
**Directory:** `src/schemas/`

- **`tickets.py`** — Enforces strict Pydantic models and Enums (`order_status`, `returns`, `subscriptions`, `other_complex`, `escalation`). Blocks free-text drift at boundaries.
- **`state.py`** — Defines `TicketResolutionState`, a unified state schema shared across all nodes containing raw text, metadata, classification results, retrieved docs, draft responses, and an immutable `audit_trail`.

### B. Specialized Agent Layer & Multi-Agent Branching
**Directory:** `src/agents/` & `src/graph/nodes.py`

- **`classifier.py`** — System prompt and routing logic for intent classification, binding Gemini to the `ClassificationResult` schema with a temperature of 0.0.
- **Refund Agent Node** — Specialized branch equipped with vector retrieval and a live database tool (`MockDatabaseService`) for real-time tracking numbers and statuses.
- **Technical Agent Node** — Specialized branch dedicated to troubleshooting technical errors and subscription support queries via targeted RAG retrieval.
- **General Agent Node** — Specialized branch handling complex policies, chit-chat, and general customer inquiries.
- **Answer Composer Node** — Unified generation module compiling context chunks to draft precise, grounded responses via `responder.py`.

### C. Orchestration & Workflow
**Directory:** `src/graph/`

- **`nodes.py`** — Modular node functions (`ingest_node`, `classify_node`, `refund_agent_node`, `technical_agent_node`, `general_agent_node`, `answer_composer_node`, `confidence_gate_node`, `handover_node`).
- **`workflow.py`** — Compiles the `StateGraph` with persistent SQLite checkpointers (`checkpoints.sqlite`), executing conditional intent routing and intercepting low-confidence or malicious tickets.

### D. Services & Core Utilities
**Directory:** `src/services/`

- **`config.py`** — Centralized configuration management handling API keys, model parameters, and thresholds.
- **`db.py`** — Simulates a live backend database service returning dynamic delivery timestamps and tracking details.
- **`llm.py`** — Unified factory function providing reusable Gemini client instances with Pydantic structured output bindings.
- **`rag.py`** — Vector store retrieval module (ChromaDB) optimized for targeted top-k chunking.
- **`guardrails.py`** — Manages prompt injection detection, PII masking, token filtering, and auto-responder detection.

### E. API & Ingestion
**Directory:** `src/api/`

- **`main.py`** — FastAPI application factory exposing secure webhook endpoints (`/webhook/email`) protected by `X-API-Key` validation headers and `slowapi` rate limiting.

---

## 4. Technical Guardrails & Data Governance

- **Structured Output Enforcement** — LLM outputs are programmatically constrained using Pydantic, ensuring type-safe processing down the graph pipeline.
- **Auditability** — Every node appends timestamped actions to the `audit_trail` list inside the workflow state for compliance and debugging.
- **Fail-Safe Escalation** — Any ticket flagged by security guardrails, prompt injection filters, or scoring below confidence thresholds is automatically intercepted and routed to the human support queue.

---

## 5. Enterprise Security & Observability Layer

1. **API Gateway & Rate Limiting** — Inbound webhooks require valid `X-API-Key` headers and are protected against abuse via `slowapi` rate-limiting middleware.
2. **OpenTelemetry Tracing** — All agent node executions, tool lookups, and state transitions are traced for telemetry auditing and observability.

---

## 6. Evaluation & Continuous Improvement Loop

- **Golden Dataset** — `tests/golden_dataset.json` stores curated test cases covering positive queries, edge cases, out-of-bounds inputs, and prompt injection attempts (`guardrail_injection`).
- **Automated CI/CD** — GitHub Actions workflows utilize the project `Makefile` to run deterministic unit, graph governance, and API security tests automatically on every push.
- **LLM-as-a-Judge** — Evaluates completed ticket responses programmatically against faithfulness and relevancy standards.
- **Human-in-the-Loop (HITL) Feedback** — Operators can submit corrected responses via the Streamlit UI webhook (`/webhook/feedback`), dynamically updating golden records and few-shot routing examples.