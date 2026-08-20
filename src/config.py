import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Centralized configuration for the Customer Support Resolution Desk."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
   
    # Model Configurations
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")
    CLASSIFIER_TEMPERATURE: float = float(os.getenv("CLASSIFIER_TEMPERATURE", "0.0"))
    RESPONDER_TEMPERATURE: float = float(os.getenv("RESPONDER_TEMPERATURE", "0.2"))
    
    # Guardrail Thresholds
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
    MAX_RAG_CHUNKS: int = int(os.getenv("MAX_RAG_CHUNKS", "2"))

settings = Settings()