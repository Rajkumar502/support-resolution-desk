from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class SupportCategory(str, Enum):
    ORDER_STATUS = "order_status"
    RETURNS = "returns"
    SUBSCRIPTIONS = "subscriptions"
    OTHER_COMPLEX = "other_complex"
    ESCALATION = "escalation"

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

class RiskAssessment(BaseModel):
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Low for standard FAQ/tracking; Medium for returns/subscriptions; High for missing items, damages, legal threats, or financial compensation demands."
    )
    requires_human_approval: bool = Field(
        description="True if the ticket involves financial risk, missing goods, emotional distress, or policy overrides."
    )
    reasoning: str = Field(description="Explanation for the assigned risk level.")

class RAGContext(BaseModel):
    chunks: List[str] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)

class TicketResolutionState(BaseModel):
    raw_email_text: str
    metadata: Optional[TicketMetadata] = None
    classification: Optional[ClassificationResult] = None
    risk_assessment: Optional[RiskAssessment] = None
    retrieved_docs: Optional[RAGContext] = None
    draft_response: Optional[str] = None
    confidence_gate_passed: bool = False
    final_output: Optional[str] = None
    escalation_reason: Optional[str] = None
    audit_trail: List[str] = Field(default_factory=list)
