import httpx
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from app.core.config import settings

logger = logging.getLogger(__name__)

class TelegramProvider(ABC):
    @abstractmethod
    async def send_text(self, chat_id: str, text: str) -> bool:
        pass

    @abstractmethod
    async def send_product(self, chat_id: str, text: str, product_name: str, product_url: str, image_url: Optional[str] = None) -> bool:
        pass

class RealTelegramProvider(TelegramProvider):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    async def send_text(self, chat_id: str, text: str) -> bool:
        if not self.token:
            return False
            
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Telegram message sent to {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False

    async def send_product(self, chat_id: str, text: str, product_name: str, product_url: str, image_url: Optional[str] = None) -> bool:
        if not self.token:
            return False
            
        message_text = f"{text}\n\n*{product_name}*\n[View Product]({product_url})"
        
        # If we have an image, send a photo with caption, otherwise send text
        url = f"{self.api_url}/sendPhoto" if image_url else f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "parse_mode": "Markdown"
        }
        
        if image_url:
            payload["photo"] = image_url
            payload["caption"] = message_text
        else:
            payload["text"] = message_text
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Telegram product sent to {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram product to {chat_id}: {e}")
            return False

class DemoTelegramProvider(TelegramProvider):
    def __init__(self):
        logger.info("Initializing Demo Telegram Provider")

    async def send_text(self, chat_id: str, text: str) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Message: {text}")
        return True

    async def send_product(self, chat_id: str, text: str, product_name: str, product_url: str, image_url: Optional[str] = None) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Product: {product_name} | URL: {product_url}")
        return True

def get_telegram_provider() -> TelegramProvider:
    if settings.TELEGRAM_BOT_TOKEN:
        return RealTelegramProvider()
    return DemoTelegramProvider()
