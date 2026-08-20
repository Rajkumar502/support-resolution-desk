import datetime
import logging
from fastapi import FastAPI, HTTPException, Security, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.graph.workflow import graph
from src.schemas.tickets import TicketResolutionState, TicketMetadata
from src.services.feedback import record_human_feedback
from src.services.security import verify_api_key

# Configure lightweight logging for observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupportDeskLogger")

# --- LIGHTWEIGHT TERMINAL TRACING INSTRUMENTATION ---
try:
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry import trace as trace_api
    from opentelemetry.sdk import trace as trace_sdk
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    tracer_provider = trace_sdk.TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace_api.set_tracer_provider(tracer_provider)
    
    LangChainInstrumentor().instrument()
    print("✅ Console OpenTelemetry tracing active.")
except Exception as e:
    print(f"⚠️ Tracing setup skipped: {e}")

app = FastAPI(
    title="Customer Support Resolution Desk API",
    description="Automated triage, RAG grounding, and confidence-gated resolution workflow.",
    version="1.0.0"
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailIngestRequest(BaseModel):
    raw_email_text: str
    sender_email: str
    subject: str
    thread_id: str = "thread_default_001"

class HumanFeedbackPayload(BaseModel):
    raw_email_text: str
    corrected_category: str
    approved_response: str

@app.post("/webhook/email", summary="Ingest incoming customer email securely")
@limiter.limit("10/minute") # Enforces max 10 requests per minute per IP address
async def ingest_email_webhook(
    request: Request, 
    payload: EmailIngestRequest, 
    api_key: str = Security(verify_api_key)
):
    """Receives email webhook securely, enforces rate limits, verifies X-API-Key, and executes LangGraph workflow."""
    try:
        initial_state = TicketResolutionState(
            raw_email_text=payload.raw_email_text,
            metadata=TicketMetadata(
                sender_email=payload.sender_email,
                subject=payload.subject,
                timestamp=str(datetime.datetime.utcnow()),
                thread_id=payload.thread_id
            ),
            audit_trail=["API webhook successfully received incoming email."]
        )
        
        # Pass checkpointer configuration with thread_id
        config = {"configurable": {"thread_id": payload.thread_id}}
        final_state = graph.invoke(initial_state, config=config)
        
        logger.info(f"Successfully processed secure ticket ID {payload.thread_id} | Category: {final_state.get('classification')}")
        
        return {
            "status": "success",
            "category": final_state["classification"].category.value if final_state.get("classification") else None,
            "confidence_score": final_state["classification"].confidence_score if final_state.get("classification") else None,
            "confidence_gate_passed": final_state.get("confidence_gate_passed"),
            "final_output": final_state.get("final_output"),
            "audit_trail": final_state.get("audit_trail", [])
        }
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.post("/webhook/feedback", summary="Capture Human-in-the-Loop Feedback")
async def handle_human_feedback(payload: HumanFeedbackPayload, api_key: str = Security(verify_api_key)):
    """Receives human operator edits on escalated tickets and updates the learning dataset securely."""
    try:
        record_human_feedback(
            raw_email_text=payload.raw_email_text,
            correct_category=payload.corrected_category,
            human_approved_response=payload.approved_response
        )
        return {"status": "success", "message": "Feedback recorded and added to self-improving training set."}
    except Exception as e:
        logger.error(f"Failed to record feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "healthy", "service": "support-resolution-desk", "model": settings.MODEL_NAME}