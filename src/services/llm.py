from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings

def get_gemini_model(temperature: float = None, structured_output_schema=None):
    """
    Centralized factory function for Gemini using global config settings.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    temp = temperature if temperature is not None else settings.CLASSIFIER_TEMPERATURE

    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temp,
    )
    
    if structured_output_schema:
        return llm.with_structured_output(structured_output_schema)
        
    return llm