import logging
from typing import Dict, Any, Optional
from app.integrations.whatsapp.provider import get_whatsapp_provider
from app.models.models import CustomerSession
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class CommunicationOrchestrator:
    def __init__(self):
        self.whatsapp_provider = get_whatsapp_provider()
    
    async def decide_and_execute(self, session: CustomerSession, intent_category: str, recommended_action: str) -> Optional[str]:
        """
        Decide the communication channel based on intent and trigger it.
        """
        if intent_category == "HIGH_PURCHASE_INTENT":
            logger.info(f"High intent detected for session {session.session_id}. Triggering communication...")
            
            # Policy: First trigger Electron Simulated Call
            await self.trigger_electron_call(session.session_id)
            
            # Policy: If there is a known user with a phone number (mocked here), send WhatsApp
            # In a real scenario we'd look up the user's phone number
            # await self.whatsapp_provider.send_text("user_phone", "Hi, I noticed you were looking at gaming laptops.")
            
            return "TRIGGERED_ELECTRON_CALL"
        return "NO_ACTION"

    async def trigger_electron_call(self, session_id: str):
        """Send a trigger to the Electron App via its exposed local IPC server/API (if it had one)."""
        logger.info(f"Triggering Electron call for session {session_id}")
        # In a real desktop-coupled system, this could be a websocket or local HTTP call.
        # For this skeleton, we just log it.
        try:
            # async with httpx.AsyncClient() as client:
            #     await client.post(f"{settings.ELECTRON_API_URL}/trigger-call", json={"session_id": session_id})
            pass
        except Exception as e:
            logger.error(f"Failed to trigger Electron: {str(e)}")
