from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from app.integrations.voice.provider import get_voice_provider
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str = ""):
    await websocket.accept()
    logger.info(f"WebSocket connection established for Voice API with session_id: {session_id}")
    
    provider = get_voice_provider()

    try:
        await provider.handle_session(websocket, session_id)
                
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in voice websocket: {e}")
        try:
            await websocket.close()
        except:
            pass
