from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import set_key, unset_key
from typing import Optional
from app.core.config import settings

router = APIRouter()

class ApiKeysUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    telegram_bot_token: Optional[str] = None

class ApiKeysResponse(BaseModel):
    gemini_api_key: Optional[str] = None
    telegram_bot_token: Optional[str] = None

def mask_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return ""
    if len(key) < 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"

@router.get("/keys", response_model=ApiKeysResponse)
async def get_api_keys():
    return ApiKeysResponse(
        gemini_api_key=mask_key(settings.GEMINI_API_KEY),
        telegram_bot_token=mask_key(settings.TELEGRAM_BOT_TOKEN)
    )

@router.post("/keys", response_model=ApiKeysResponse)
async def update_api_keys(keys: ApiKeysUpdate):
    # __file__ is in backend/app/api/v1/endpoints/system.py
    # We need to go up 5 levels to reach the backend directory
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 
        ".env"
    )
    
    if keys.gemini_api_key is not None and keys.gemini_api_key != mask_key(settings.GEMINI_API_KEY):
        if keys.gemini_api_key.strip() == "":
            settings.GEMINI_API_KEY = None
            unset_key(env_path, "GEMINI_API_KEY")
        else:
            settings.GEMINI_API_KEY = keys.gemini_api_key.strip()
            set_key(env_path, "GEMINI_API_KEY", settings.GEMINI_API_KEY)
            
    if keys.telegram_bot_token is not None and keys.telegram_bot_token != mask_key(settings.TELEGRAM_BOT_TOKEN):
        if keys.telegram_bot_token.strip() == "":
            settings.TELEGRAM_BOT_TOKEN = None
            unset_key(env_path, "TELEGRAM_BOT_TOKEN")
        else:
            settings.TELEGRAM_BOT_TOKEN = keys.telegram_bot_token.strip()
            set_key(env_path, "TELEGRAM_BOT_TOKEN", settings.TELEGRAM_BOT_TOKEN)
            
    return ApiKeysResponse(
        gemini_api_key=mask_key(settings.GEMINI_API_KEY),
        telegram_bot_token=mask_key(settings.TELEGRAM_BOT_TOKEN)
    )
