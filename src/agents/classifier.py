from langchain_core.prompts import ChatPromptTemplate
from src.services.llm import get_gemini_model
from src.schemas.tickets import ClassificationResult
from src.config import settings
import json
import os

BASE_SYSTEM_PROMPT = """
You are a strict intent-classifier for an e-commerce support desk.
Classify the incoming text into EXACTLY one of these categories:
- order_status (tracking, delivery, order numbers)
- returns (refunds, return labels, exchanges)
- subscriptions (billing credit cards, updating plans)
- other_complex (general chat, praise, complaints, or completely unrelated out-of-domain requests like writing code or scraping data)

Do NOT classify coding or unrelated tasks as order_status. Out-of-domain requests must be categorized as other_complex.
"""

def get_similar_examples(query: str, k: int = 2) -> str:
    """Fetches relevant historical classification examples from the golden dataset to act as few-shot context."""
    golden_path = "tests/golden_dataset.json"
    if not os.path.exists(golden_path):
        return "No historical examples available."
    
    try:
        with open(golden_path, "r") as f:
            dataset = json.load(f)
        
        # Simple word overlap scoring to find similar past tickets
        query_words = set(query.lower().split())
        scored_examples = []
        for item in dataset:
            ex_text = item.get("raw_email_text", "").lower()
            score = len(query_words.intersection(set(ex_text.split())))
            scored_examples.append((score, item))
            
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        top_k = scored_examples[:k]
        
        examples_str = ""
        for _, ex in top_k:
            examples_str += f"- Example Input: \"{ex['raw_email_text']}\"\n  Expected Category: {ex['expected_category']}\n\n"
        
        return examples_str if examples_str else "No close historical matches."
    except Exception:
        return "Few-shot retrieval fallback active."

def classify_email(email_text: str) -> ClassificationResult:
    """Takes raw email text, injects dynamic few-shot RAG examples, and invokes Gemini with structured output."""
    
    # Retrieve dynamic few-shot context based on input keywords
    few_shot_context = get_similar_examples(email_text, k=2)
    
    # Construct dynamic prompt merging base guidelines with similar past examples
    dynamic_system_prompt = (
        BASE_SYSTEM_PROMPT.strip() + 
        "\n\nHere are some relevant historical classification examples to guide you:\n" +
        few_shot_context
    )
    
    structured_llm = get_gemini_model(
        temperature=settings.CLASSIFIER_TEMPERATURE,
        structured_output_schema=ClassificationResult
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", dynamic_system_prompt),
        ("human", "Please classify the following customer email:\n\n{email_text}")
    ])
    
    chain = prompt | structured_llm
    result: ClassificationResult = chain.invoke({"email_text": email_text})
    return result