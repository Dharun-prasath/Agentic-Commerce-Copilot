from abc import ABC, abstractmethod
from typing import AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings
import logging
import asyncio
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import CustomerSession
from sqlalchemy.orm import selectinload

from app.agents.product_intelligence.agent import search_products, get_product_details
from app.agents.commerce.agent import get_cart_status, add_product_to_cart
import json

class VoiceProvider(ABC):
    @abstractmethod
    async def handle_session(self, websocket: WebSocket, session_id: str = ""):
        pass

class GeminiNativeAudioProvider(VoiceProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.LLM_MODEL or "gemini-2.5-flash-native-audio-latest"
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"Initializing Gemini Native Audio with model {self.model}")

    async def handle_session(self, websocket: WebSocket, session_id: str = ""):
        try:
            context_str = ""
            if session_id:
                async for db in get_db():
                    result = await db.execute(
                        select(CustomerSession)
                        .options(selectinload(CustomerSession.customer))
                        .where(CustomerSession.id == session_id)
                    )
                    db_session = result.scalar_one_or_none()
                    if db_session:
                        context_str = f"User session ID is {session_id}."
                        if db_session.customer:
                            context_str += f" Customer name is {db_session.customer.name}, phone: {db_session.customer.phone}."
                    break

            base_instruction = "You are a helpful AI Voice Assistant for Razorpay Agentic Commerce. You are taking a phone call with a user. Keep your responses extremely concise. 1-2 short sentences max. Talk naturally like a real human on the phone. Start by greeting the user!"
            
            system_instruction_text = base_instruction
            if context_str:
                system_instruction_text += f"\n\nContext:\n{context_str}"

            tool_declarations = types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="search_products",
                        description="Search for products in the catalog",
                        parameters={
                            "type": "OBJECT",
                            "properties": {
                                "query": {"type": "STRING", "description": "Search query"},
                                "category": {"type": "STRING", "description": "Optional category"}
                            },
                            "required": ["query"]
                        }
                    ),
                    types.FunctionDeclaration(
                        name="get_product_details",
                        description="Get details for a specific product ID",
                        parameters={
                            "type": "OBJECT",
                            "properties": {
                                "product_id": {"type": "STRING", "description": "Product ID"}
                            },
                            "required": ["product_id"]
                        }
                    ),
                    types.FunctionDeclaration(
                        name="get_cart_status",
                        description="Get the status of the user's cart",
                        parameters={
                            "type": "OBJECT",
                            "properties": {}
                        }
                    ),
                    types.FunctionDeclaration(
                        name="add_product_to_cart",
                        description="Add a product to the cart",
                        parameters={
                            "type": "OBJECT",
                            "properties": {
                                "product_id": {"type": "STRING"},
                                "quantity": {"type": "INTEGER"}
                            },
                            "required": ["product_id", "quantity"]
                        }
                    )
                ]
            )

            config = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                system_instruction=types.Content(parts=[types.Part.from_text(text=system_instruction_text)]),
                tools=[tool_declarations],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Puck"
                        )
                    )
                )
            )
            
            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                logger.info("Connected to Gemini Live API")
                
                # Trigger the AI to speak first by sending a small audio clip of someone saying "hello"
                import os
                hello_path = os.path.join(os.path.dirname(__file__), "hello.pcm")
                if os.path.exists(hello_path):
                    with open(hello_path, "rb") as f:
                        audio_data = f.read()
                    await session.send_realtime_input(
                        audio={"mime_type": "audio/pcm;rate=16000", "data": audio_data}
                    )
                    logger.info("Sent initial audio greeting trigger to Gemini")
                
                async def send_to_gemini():
                    try:
                        while True:
                            # Receive raw PCM bytes from the client
                            data = await websocket.receive_bytes()
                            if not data:
                                break
                            
                            # Log every ~5th chunk to avoid spamming the console
                            if getattr(self, '_chunk_counter', 0) % 5 == 0:
                                logger.info(f"Received audio from user: {len(data)} bytes, sending to Gemini...")
                            self._chunk_counter = getattr(self, '_chunk_counter', 0) + 1
                            
                            # Send to Gemini
                            await session.send_realtime_input(
                                audio={"mime_type": "audio/pcm;rate=16000", "data": data}
                            )
                    except WebSocketDisconnect:
                        logger.info("Client WebSocket disconnected.")
                    except Exception as e:
                        logger.error(f"Error in send_to_gemini: {e}")

                async def receive_from_gemini():
                    while True:
                        try:
                            async for response in session.receive():
                                if response.server_content and response.server_content.model_turn and response.server_content.model_turn.parts:
                                    for part in response.server_content.model_turn.parts:
                                        if part.inline_data and part.inline_data.data is not None:
                                            # Avoid logging every chunk to reduce spam, log occasionally
                                            if getattr(session, '_recv_chunk_counter', 0) % 20 == 0:
                                                logger.info(f"Received audio chunk from Gemini: {len(part.inline_data.data)} bytes")
                                            session._recv_chunk_counter = getattr(session, '_recv_chunk_counter', 0) + 1
                                            await websocket.send_bytes(part.inline_data.data)
                                
                                if response.tool_call:
                                    function_responses = []
                                    for call in response.tool_call.function_calls:
                                        logger.info(f"Gemini requested tool: {call.name}")
                                        args = call.args or {}
                                        try:
                                            if call.name == "search_products":
                                                result = await search_products.ainvoke(args)
                                            elif call.name == "get_product_details":
                                                result = await get_product_details.ainvoke(args)
                                            elif call.name == "get_cart_status":
                                                args["session_id"] = session_id
                                                result = await get_cart_status.ainvoke(args)
                                            elif call.name == "add_product_to_cart":
                                                args["session_id"] = session_id
                                                result = await add_product_to_cart.ainvoke(args)
                                            else:
                                                result = "Unknown tool"
                                                
                                            # Return dict wrapped in result
                                            function_responses.append(
                                                types.FunctionResponse(
                                                    name=call.name,
                                                    id=call.id,
                                                    response={"result": result}
                                                )
                                            )
                                        except Exception as e:
                                            logger.error(f"Error executing tool {call.name}: {e}")
                                            function_responses.append(
                                                types.FunctionResponse(
                                                    name=call.name,
                                                    id=call.id,
                                                    response={"error": str(e)}
                                                )
                                            )
                                    
                                    await session.send(input=types.LiveClientToolResponse(function_responses=function_responses))

                        except Exception as e:
                            err_str = str(e)
                            if "1000" in err_str or "1001" in err_str or "closed" in err_str.lower():
                                logger.info("Gemini Live API connection closed normally.")
                                break
                            logger.error(f"Error in receive_from_gemini: {e}")
                            await asyncio.sleep(0.1) # Prevents tight loops on persistent errors

                # Run both tasks concurrently
                await asyncio.gather(send_to_gemini(), receive_from_gemini())

        except Exception as e:
            logger.error(f"Failed to handle Gemini Live session: {e}")

class DemoVoiceProvider(VoiceProvider):
    def __init__(self):
        logger.info("Initializing Demo Voice Provider")

    async def handle_session(self, websocket: WebSocket, session_id: str = ""):
        try:
            while True:
                data = await websocket.receive_bytes()
                await asyncio.sleep(0.5)
                await websocket.send_bytes(b'demo_audio_response')
        except WebSocketDisconnect:
            pass

def get_voice_provider() -> VoiceProvider:
    if settings.VOICE_MODE == "real":
        return GeminiNativeAudioProvider()
    return DemoVoiceProvider()
