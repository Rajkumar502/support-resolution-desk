from enum import Enum
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
