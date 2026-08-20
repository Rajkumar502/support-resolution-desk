from langchain_core.prompts import ChatPromptTemplate
from src.services.llm import get_gemini_model
from src.config import settings


RESPONDER_SYSTEM_PROMPT = """
You are a professional, helpful customer support AI agent for an e-commerce platform.
Your job is to draft a polite, direct response to the customer using the provided Knowledge Base (RAG Context).

Guidelines:
1. Use the facts provided in the RAG Context to answer the user's question directly (e.g., mention shipping timeframes, return windows, or subscription steps).
2. Do not invent fake tracking numbers or live database info, but DO use the general policies from the RAG context to be as helpful as possible.
3. Keep the tone warm, empathetic, and professional.
"""

def generate_draft_response(email_text: str, category: str, retrieved_chunks: list[str]) -> str:
    """Generates a RAG-grounded draft response using centralized Gemini settings."""
    llm = get_gemini_model(temperature=settings.RESPONDER_TEMPERATURE)
    
    context_str = "\n".join([f"- {chunk}" for chunk in retrieved_chunks])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESPONDER_SYSTEM_PROMPT),
        ("human", "Customer Inquiry Category: {category}\n\nCustomer Email:\n{email_text}\n\nRetrieved Knowledge Base Context:\n{context}\n\nDraft a helpful response:")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "category": category,
        "email_text": email_text,
        "context": context_str
    })
    
    # Robustly handle content whether it comes back as a string, list, or AIMessage object
    content = getattr(response, "content", response)
    if isinstance(content, list):
        # Extract text from structured content blocks if returned as a list
        text_parts = [item.get("text", "") if isinstance(item, dict) else str(item) for item in content]
        return "".join(text_parts)
        
    return str(content)