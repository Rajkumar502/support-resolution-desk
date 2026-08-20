from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from src.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """Validates the incoming X-API-Key header against system environment configs."""
    expected_key = getattr(settings, "API_SECRET_KEY", "secret-support-desk-key")
    
    if api_key == expected_key or not expected_key:
        return api_key
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials. Invalid or missing X-API-Key header."
    )