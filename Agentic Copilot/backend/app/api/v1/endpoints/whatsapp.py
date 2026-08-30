from fastapi import APIRouter, Request, Response, HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    """Verify webhook for WhatsApp Business Cloud API."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp Webhook verified successfully!")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    
    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/webhook")
async def receive_webhook(request: Request):
    """Receive messages from WhatsApp."""
    try:
        body = await request.json()
        logger.info(f"WhatsApp webhook received: {body}")
        
        # We would process incoming messages and route them to LangGraph / SalesAgent here
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
