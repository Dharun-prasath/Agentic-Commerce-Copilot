from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    COPILOT_DATABASE_URL: str = "postgresql+asyncpg://copilot:copilot_pass@localhost:5435/copilot_db"
    COMMERCE_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/agentic_commerce"
    REDIS_URL: str = "redis://localhost:6380"
    
    DEMO_APP_BASE_URL: str = "http://localhost:8001/api/v1"
    
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-2.5-flash-native-audio-latest"
    GEMINI_API_KEY: Optional[str] = None
    
    INTENT_AGENT_MODEL: Optional[str] = "gemini-2.5-flash"
    PRODUCT_AGENT_MODEL: Optional[str] = "gemini-2.5-flash"
    SALES_AGENT_MODEL: Optional[str] = "gemini-2.5-flash"
    COMMERCE_AGENT_MODEL: Optional[str] = "gemini-2.5-flash"
    VOICE_AGENT_MODEL: Optional[str] = None
    
    WHATSAPP_MODE: str = "demo"
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v17.0"
    
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    
    VOICE_MODE: str = "real"
    VOICE_PROVIDER: str = "gemini-native-audio"
    
    JWT_SECRET: str = "secret"
    JWT_EXPIRE_MINUTES: int = 10080
    
    ELECTRON_API_URL: str = "http://localhost:5174"
    
    DASHBOARD_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
