from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/agentic_commerce"

    # Security
    JWT_SECRET: str = "change-this-to-a-random-secret-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # Razorpay (optional — app works without them for non-payment features)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # Tax
    TAX_RATE: float = 0.18

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def razorpay_configured(self) -> bool:
        """Returns True only when both Razorpay credentials are provided."""
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

    @property
    def async_database_url(self) -> str:
        """Convert sync postgresql:// URL to async postgresql+asyncpg:// URL."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
