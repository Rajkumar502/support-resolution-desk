# 🤖 Support Resolution Desk (Agentic AI Workflow)

A production-grade, multi-agent customer support resolution desk powered by **LangGraph**, **Google Gemini**, **FastAPI**, and **Streamlit**.

This application automates customer support tickets through an intelligent workflow featuring intent classification, RAG knowledge retrieval, confidence gating, security guardrails, PII masking, and persistent SQLite thread memory.

---

## ✨ Key Features

- **Multi-Agent State Graph** — Orchestrated using LangGraph with specialized nodes for ingestion, classification, RAG retrieval, response generation, and confidence gating.
- **Security & Governance Guardrails** — Built-in detection for prompt injection/jailbreak attempts, auto-responder loops, and automatic PII masking.
- **Persistent Thread Memory** — Backed by a SQLite checkpointer (`checkpoints.sqlite`) to maintain conversation history across multiple requests.
- **Dual Interfaces:**
  - **Interactive Streamlit Dashboard** for visual testing, real-time feedback, and audit trail inspection.
  - **FastAPI Backend** for programmatic integration and production API deployment.
- **Robust Test Suite** — Comprehensive unit and governance tests covering positive paths, edge cases, neutral inquiries, and adversarial safety guardrails.

---

## 🛠️ Project Structure

```text
support-resolution-desk/
├── src/
│   ├── agents/            # Specialized Gemini agents (classifier, responder)
│   ├── api/                # FastAPI backend server
│   ├── graph/               # LangGraph workflow definitions & nodes
│   ├── schemas/             # Pydantic data models & state definitions
│   └── services/            # RAG retrieval & guardrail services
├── tests/                   # Unit, integration, and governance test cases
├── app_ui.py                 # Streamlit dashboard interface
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Multi-service container orchestration
├── Makefile                   # Convenient automation commands
└── requirements.txt           # Python project dependencies
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites & Installation

Ensure you have Python 3.11+ installed. Clone the repository, set up a virtual environment, and install dependencies:

```bash
git clone https://github.com/your-username/support-resolution-desk.git
cd support-resolution-desk

python3 -m venv venv
source venv/bin/activate
make install
```

### 2. Set Your API Key

Export your Google Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

---

## 💻 Running the Application

### Option A: Local Development Server

**Launch the Streamlit Dashboard:**

```bash
make ui
```
Access the web interface at `http://localhost:8501`.

**Start the FastAPI Backend:**

```bash
make run
```
Access interactive docs at `http://localhost:8000/docs`.

### Option B: Running with Docker & Docker Compose

You can containerize and run both services together seamlessly:

```bash
make docker-build
make docker-up
```

- **Streamlit UI:** `http://localhost:8501`
- **FastAPI Backend:** `http://localhost:8000/docs`

To stop Docker containers:

```bash
make docker-down
```

---

## 🧪 Running Tests & Evaluation

To execute the complete verification test suite (covering positive paths, negative out-of-bounds, neutral queries, edge cases, and prompt-injection security guardrails):

```bash
make test
```

To run the golden dataset evaluation benchmark:

```bash
make eval
```

## 🧪 Run Benchmarks

```bash
make benchmark
```

## 🔒 Enterprise Security & Rate Limiting
To ensure production readiness, the FastAPI backend includes:
* **API Key Authentication**: Inbound requests to `/webhook/email` require a valid `X-API-Key` header verified via custom middleware.
* **Rate Limiting**: Integrated using `slowapi` to restrict webhooks to a safe threshold (default: 10 requests/minute per IP) preventing abuse or automated scraping.

## 🤖 Automated LLM Evaluation Pipeline
We utilize an automated evaluation suite (`evaluate_rag.py`) leveraging a custom **Gemini-as-a-Judge** framework to score our multi-agent outputs without relying on external third-party evaluation keys:
* **Faithfulness Score**: Measures whether the Answer Composer's output is strictly grounded in retrieved database/RAG chunks (checking for hallucinations).
* **Answer Relevancy Score**: Measures how directly and completely the response addresses the user's initial inquiry.

Run the evaluation suite via:
```bash
make evaluate
```

---

## 📋 Available Make Commands

| Command | Description |
|---|---|
| `make install` | Installs project dependencies from `requirements.txt`. |
| `make test` | Runs the full pytest suite (classifiers, graph workflows, and governance). |
| `make eval` | Runs the golden dataset evaluation benchmark. |
| `make run` | Starts the FastAPI production/development server. |
| `make ui` | Launches the interactive Streamlit Dashboard. |
| `make benchmark` | Runs empirical token and latency benchmarks. |
| `make docker-build` | Builds Docker images for API and UI services. |
| `make docker-up` | Starts Docker containers in detached mode. |
| `make docker-logs` | Streams live container logs. |
| `make docker-down` | Stops and removes Docker containers. |
| `make clean` | Removes cache artifacts, virtual environments, and SQLite databases. |