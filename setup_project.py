import os
from pathlib import Path

# Define directory structure and initial placeholder contents
DIRECTORY_STRUCTURE = {
    "src": {
        "__init__.py": "",
        "config.py": "# Application configuration settings\n",
        "schemas": {
            "__init__.py": "",
            "tickets.py": '''from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class SupportCategory(str, Enum):
    ORDER_STATUS = "order_status"
    RETURNS = "returns"
    SUBSCRIPTIONS = "subscriptions"
    OTHER_COMPLEX = "other_complex"

class TicketMetadata(BaseModel):
    sender_email: str
    subject: str
    timestamp: str
    thread_id: str
    is_auto_responder: bool = False

class ClassificationResult(BaseModel):
    category: SupportCategory
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

class RAGContext(BaseModel):
    chunks: List[str] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)

class TicketResolutionState(BaseModel):
    raw_email_text: str
    metadata: Optional[TicketMetadata] = None
    classification: Optional[ClassificationResult] = None
    retrieved_docs: Optional[RAGContext] = None
    draft_response: Optional[str] = None
    confidence_gate_passed: bool = False
    final_output: Optional[str] = None
    escalation_reason: Optional[str] = None
    audit_trail: List[str] = Field(default_factory=list)
''',
            "state.py": "# Graph state definitions\n"
        },
        "agents": {
            "__init__.py": "",
            "classifier.py": "# Classifier agent prompt and logic\n",
            "responder.py": "# Responder agent logic\n"
        },
        "graph": {
            "__init__.py": "",
            "workflow.py": "# LangGraph workflow compilation\n",
            "nodes.py": "# Graph node definitions\n"
        },
        "services": {
            "__init__.py": "",
            "llm.py": "# Gemini Pro client wrapper\n",
            "rag.py": "# Vector database RAG service\n",
            "guardrails.py": "# PII and safety guardrails\n"
        },
        "api": {
            "__init__.py": "",
            "main.py": "# FastAPI application factory\n",
            "webhooks.py": "# Email webhook ingestion\n"
        }
    },
    "tests": {
        "__init__.py": "",
        "golden_dataset.json": "[]\n",
        "test_classifier.py": "# Unit tests for classifier\n",
        "test_graph.py": "# End-to-end graph tests\n"
    }
}

ROOT_FILES = {
    ".env.example": "GEMINI_API_KEY=your_gemini_api_key_here\nLANGSMITH_API_KEY=your_langsmith_api_key_here\n",
    "requirements.txt": "langgraph>=0.2.0\nlangchain-google-genai>=2.0.0\nlangchain-core>=0.3.0\npydantic>=2.0.0\nfastapi>=0.110.0\nuvicorn>=0.28.0\nchromadb>=0.4.24\npython-dotenv>=1.0.1\nlangsmith>=0.1.0\nrequests>=2.31.0\n",
    "langgraph.json": '{\n  "graphs": {\n    "support_desk": "src.graph.workflow:graph"\n  },\n  "env": ".env"\n}\n'
}

def create_structure(base_path: Path, structure: dict):
    for name, content in structure.items():
        current_path = base_path / name
        if isinstance(content, dict):
            current_path.mkdir(parents=True, exist_ok=True)
            create_structure(current_path, content)
        else:
            current_path.parent.mkdir(parents=True, exist_ok=True)
            if not current_path.exists():
                with open(current_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Created file: {current_path}")
            else:
                print(f"Skipped (already exists): {current_path}")

def main():
    base = Path(".")
    print("Initializing Customer Support Resolution Desk project structure...")
    create_structure(base, DIRECTORY_STRUCTURE)
    
    for filename, content in ROOT_FILES.items():
        f_path = base / filename
        if not f_path.exists():
            with open(f_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created root file: {f_path}")
        else:
            print(f"Skipped (already exists): {f_path}")
            
    print("\nProject structure setup completed successfully!")

if __name__ == "__main__":
    main()