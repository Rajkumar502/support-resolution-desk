from src.schemas.tickets import TicketResolutionState, TicketMetadata, SupportCategory, ClassificationResult, RiskAssessment
from src.agents.classifier import classify_email
from src.services.rag import retrieve_knowledge_base_docs
from src.agents.responder import generate_draft_response
from src.services.guardrails import GuardrailsService
from src.services.rules_manager import RulesManager
from src.services.system_status import MockSystemStatusService
from src.config import settings
import datetime
import re
from src.services.db import MockDatabaseService

def ingest_node(state: TicketResolutionState) -> TicketResolutionState:
    """Pre-processes incoming email, checks security guardrails, masks PII, and initializes metadata."""
    print("--- NODE: INGEST_NODE ---")
    
    if not state.metadata:
        state.metadata = TicketMetadata(
            sender_email="customer@example.com",
            subject="Support Inquiry",
            timestamp=str(datetime.datetime.utcnow()),
            thread_id="thread_mock_123"
        )
    
    # 1. Prompt Injection Guardrail check
    if GuardrailsService.detect_prompt_injection(state.raw_email_text):
        state.audit_trail.append("Security Alert: Prompt injection pattern detected! Halting to human handover.")
        state.confidence_gate_passed = False
        state.escalation_reason = "Potential prompt injection detected."
        state.classification = ClassificationResult(
            category=SupportCategory.ESCALATION,
            confidence_score=0.0,
            reasoning="Security guardrail tripped due to prompt injection pattern."
        )
        # CRITICAL: Ensure we set final output and return immediately so it doesn't classify!
        state.final_output = "[SECURITY ALERT]: Request halted due to suspected prompt injection. Routed to human security queue."
        return state

    # 2. Auto-responder loop guardrail check
    if GuardrailsService.is_auto_responder(state.metadata.subject, state.raw_email_text):
        state.audit_trail.append("Auto-responder detected. Halting automated workflow.")
        state.confidence_gate_passed = False
        state.escalation_reason = "Automated out-of-office reply."
        state.classification = ClassificationResult(
            category=SupportCategory.OTHER_COMPLEX,
            confidence_score=0.0,
            reasoning="Automated out-of-office notification."
        )
        return state
        
    # 3. Mask PII for compliance
    state.raw_email_text = GuardrailsService.mask_pii(state.raw_email_text)
    state.audit_trail.append("Email ingested, security checked, and PII masked successfully.")
    return state


def classify_node(state: TicketResolutionState) -> TicketResolutionState:
    """Invokes the Gemini classification agent (Intent Classifier)."""
    print("--- NODE: INTENT_CLASSIFIER ---")
    classification = classify_email(state.raw_email_text)
    state.classification = classification
    state.audit_trail.append(f"Classified as '{classification.category.value}' with confidence {classification.confidence_score}.")
    return state


# --- SPECIALIST AGENTS (Multi-Agent Branching) ---

def refund_agent_node(state: TicketResolutionState) -> TicketResolutionState:
    """Specialized agent for order tracking & refunds: Equipped with database access + RAG."""
    print("--- NODE: REFUND AGENT (DB Tool Enabled) ---")
    
    text = state.raw_email_text
    
    # 1. Extract order ID if present (e.g., #12345)
    order_match = re.search(r"#\d+", text)
    db_context_str = ""
    
    if order_match:
        order_id = order_match.group(0)
        print(f"🔍 [DB TOOL] Found order ID: {order_id}. Querying database...")
        order_data = MockDatabaseService.fetch_order_details(order_id)
        
        db_context_str = (
            f"\n[LIVE DATABASE RECORD FOR {order_id}]:\n"
            f"- Status: {order_data['status']}\n"
            f"- Carrier: {order_data['carrier']}\n"
            f"- Tracking Number: {order_data['tracking_number']}\n"
            f"- Est. Delivery: {order_data['estimated_delivery']}\n"
        )
        state.audit_trail.append(f"Refund Agent queried database for {order_id}: status '{order_data['status']}'.")
    else:
        state.audit_trail.append("Refund Agent executed: No order ID found for database lookup.")

    # 2. Retrieve standard RAG policy docs for returns/orders
    rag_context = retrieve_knowledge_base_docs("returns", text, top_k=settings.MAX_RAG_CHUNKS)
    
    # 3. Inject live database data directly into the RAG context chunks
    if db_context_str:
        rag_context.chunks.insert(0, db_context_str)
        
    state.retrieved_docs = rag_context
    return state


def technical_agent_node(state: TicketResolutionState) -> TicketResolutionState:
    """Specialized agent for technical troubleshooting: Equipped with live system status checks + RAG."""
    print("--- NODE: TECHNICAL AGENT (Status Tool Enabled) ---")
    
    text = state.raw_email_text.lower()
    tech_context_str = ""
    
    # Check if the user's issue relates to payments, login, or cloud errors
    if any(keyword in text for keyword in ["payment", "billing", "card", "error", "down", "login", "fail", "issue"]):
        print("🔍 [SYSTEM STATUS TOOL] Checking live infrastructure health...")
        status_data = MockSystemStatusService.check_service_status()
        
        tech_context_str = (
            f"\n[LIVE SYSTEM STATUS CHECK]:\n"
            f"- Payment Gateway: {status_data['payment_gateway']['status']} (Latency: {status_data['payment_gateway']['latency_ms']}ms)\n"
            f"- Authentication: {status_data['user_authentication']['status']}\n"
            f"- Cloud API: {status_data['cloud_api']['status']} | Note: {status_data['cloud_api']['incident']}\n"
        )
        state.audit_trail.append("Technical Agent queried live system status service.")
    else:
        state.audit_trail.append("Technical Agent executed: Standard subscription & technical RAG lookup.")

    # Retrieve standard RAG policy docs for subscriptions/technical guides
    rag_context = retrieve_knowledge_base_docs("subscriptions", state.raw_email_text, top_k=settings.MAX_RAG_CHUNKS)
    
    # Inject live system status context into the RAG chunks if available
    if tech_context_str:
        rag_context.chunks.insert(0, tech_context_str)
        
    state.retrieved_docs = rag_context
    return state


def general_agent_node(state: TicketResolutionState) -> TicketResolutionState:
    """Specialized agent for general policy and complex inquiries."""
    print("--- NODE: GENERAL AGENT ---")
    rag_context = retrieve_knowledge_base_docs("other_complex", state.raw_email_text, top_k=settings.MAX_RAG_CHUNKS)
    state.retrieved_docs = rag_context
    state.audit_trail.append("General Agent retrieved policy documentation.")
    return state


def answer_composer_node(state: TicketResolutionState) -> TicketResolutionState:
    """Unified composer that builds a grounded draft from whichever specialist ran."""
    print("--- NODE: ANSWER COMPOSER ---")
    chunks = state.retrieved_docs.chunks if state.retrieved_docs else []
    category_val = state.classification.category.value if state.classification else "general"
    
    draft = generate_draft_response(state.raw_email_text, category_val, chunks)
    state.draft_response = draft
    state.audit_trail.append("Answer Composer generated grounded draft response.")
    return state


def confidence_gate_node(state: TicketResolutionState) -> TicketResolutionState:
    """Evaluates confidence score against decoupled rules and handles greetings autonomously."""
    print("--- NODE: CONFIDENCE_GATE_NODE ---")
    
    # (Do not check 'not state.confidence_gate_passed' here, since it defaults to False).
    if state.escalation_reason:
        state.confidence_gate_passed = False
        state.audit_trail.append("Confidence gate bypassed: Prior security or risk flag enforced.")
        return state

    category = state.classification.category.value if state.classification else "other_complex"
    confidence = state.confidence_score if hasattr(state, "confidence_score") and state.confidence_score is not None else (state.classification.confidence_score if state.classification else 0.0)
    text_lower = state.raw_email_text.lower()
    
    # Handle general greetings autonomously
    greetings = ["hello", "hi ", "hey", "good morning", "good afternoon", "how are you"]
    if any(g in text_lower for g in greetings) and len(text_lower.split()) < 8:
        state.confidence_gate_passed = True
        state.draft_response = "Hello! Thanks for reaching out. How can I assist you with your orders, returns, or subscriptions today?"
        state.final_output = state.draft_response
        state.audit_trail.append("General greeting detected. Handled autonomously.")
        return state

    # Check decoupled business rules
    threshold = RulesManager.get_confidence_threshold(category)
    force_escalate = RulesManager.should_force_escalation(category)
    
    if force_escalate or confidence < threshold:
        state.confidence_gate_passed = False
        state.escalation_reason = f"Low confidence ({confidence} < {threshold}) or forced category escalation."
        state.audit_trail.append("Confidence gate FAILED. Routing to human handover queue.")
    else:
        state.confidence_gate_passed = True
        state.final_output = state.draft_response
        state.audit_trail.append("Confidence gate PASSED. Auto-reply approved.")
        
    return state


def handover_node(state: TicketResolutionState) -> TicketResolutionState:
    """Packages ticket for human agent escalation queue with HITL-ready context."""
    print("--- NODE: HUMAN QUEUE / HANDOVER ---")
    reason = state.escalation_reason or "Low confidence score or complex query requirement."
    
    state.confidence_gate_passed = False
    state.final_output = (
        f"[ESCALATED TO HUMAN SUPPORT]\n"
        f"Reason: {reason}\n"
        f"Assigned Category: {state.classification.category.value if state.classification else 'Unknown'}\n"
        f"Original Message: {state.raw_email_text}"
    )
    state.audit_trail.append(f"Ticket escalated to human support queue. Reason: {reason}")
    return state


def risk_assessment_node(state: TicketResolutionState) -> TicketResolutionState:
    """Semantically evaluates the customer email for risk, financial exposure, or abuse."""
    print("--- NODE: RISK_ASSESSMENT ---")
    
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Use settings.MODEL_NAME as defined in your config.py
    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=0.0,
        google_api_key=settings.GEMINI_API_KEY
    )
    structured_llm = llm.with_structured_output(RiskAssessment)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI safety and risk officer for an e-commerce platform support desk. "
                   "Analyze the customer message for risk factors such as missing items, broken/damaged goods, "
                   "financial compensation demands, angry disputes, or potential policy exploits."),
        ("human", "Customer Message:\n{email_text}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        assessment = chain.invoke({"email_text": state.raw_email_text})
        state.risk_assessment = assessment
        
        # If high risk or requires human approval, automatically force confidence gate failure
        if assessment.requires_human_approval or assessment.risk_level == "high":
            state.confidence_gate_passed = False
            state.escalation_reason = f"High risk detected: {assessment.reasoning}"
            state.audit_trail.append(f"Risk Guardrail Flagged: {assessment.reasoning} (Routed to Human)")
        else:
            state.audit_trail.append(f"Risk Guardrail Passed: Low/Medium risk ({assessment.risk_level}).")
            
    except Exception as e:
        # Fail-safe: if risk check fails for any reason, force human escalation to be safe
        state.confidence_gate_passed = False
        state.escalation_reason = f"Risk assessment error fallback: {str(e)}"
        state.audit_trail.append(f"Risk Guardrail Error: {str(e)} (Fallback to Human)")
        
    return state