from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    # If no API key is configured in settings, we allow it (for dev mode)
    # But for a real prod app, you'd mandate it.
    if not settings.DASHBOARD_API_KEY:
        return True
        
    if api_key == settings.DASHBOARD_API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
