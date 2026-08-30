from abc import ABC, abstractmethod
import httpx
from typing import Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppProvider(ABC):
    @abstractmethod
    async def send_text(self, to: str, text: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def send_product_link(self, to: str, product_name: str, product_url: str, description: str) -> Dict[str, Any]:
        pass

class WhatsAppCloudProvider(WhatsAppProvider):
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.version = settings.WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}"
        
    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.access_token or not self.phone_number_id:
            logger.error("WhatsApp credentials are not configured.")
            return {"status": "error", "message": "Not Configured"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp API error: {e.response.text}")
                return {"status": "error", "message": e.response.text}
            except Exception as e:
                logger.error(f"WhatsApp Request failed: {str(e)}")
                return {"status": "error", "message": str(e)}

    async def send_text(self, to: str, text: str) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        return await self._post(payload)

    async def send_product_link(self, to: str, product_name: str, product_url: str, description: str) -> Dict[str, Any]:
        text = f"*{product_name}*\n\n{description}\n\nView here: {product_url}"
        return await self.send_text(to, text)

class DemoWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        logger.info("Initializing Demo WhatsApp Provider")
        
    async def send_text(self, to: str, text: str) -> Dict[str, Any]:
        logger.info(f"[DEMO WHATSAPP] To: {to} | Message: {text}")
        return {"status": "success", "demo_mode": True, "to": to}

    async def send_product_link(self, to: str, product_name: str, product_url: str, description: str) -> Dict[str, Any]:
        logger.info(f"[DEMO WHATSAPP] To: {to} | Product: {product_name} | URL: {product_url}")
        return {"status": "success", "demo_mode": True, "to": to}

def get_whatsapp_provider() -> WhatsAppProvider:
    if settings.WHATSAPP_MODE == "real":
        return WhatsAppCloudProvider()
    return DemoWhatsAppProvider()
