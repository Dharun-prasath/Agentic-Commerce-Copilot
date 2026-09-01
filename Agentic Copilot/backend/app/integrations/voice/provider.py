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

from app.agents.sales_consultant.agent import SalesConsultantAgent
from app.integrations.voice.events import get_voice_queue, cleanup_voice_queue
from app.services.orchestrator.service import OrchestratorService

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
                        .options(selectinload(CustomerSession.customer), selectinload(CustomerSession.intents))
                        .where(CustomerSession.session_id == session_id)
                    )
                    db_session = result.scalar_one_or_none()
                    if db_session:
                        context_str = f"User session ID is {session_id}."
                        if db_session.customer:
                            context_str += f" Customer name is {db_session.customer.name}, phone: {db_session.customer.phone}."
                        if db_session.intents:
                            latest_intent = db_session.intents[-1]
                            context_str += f"\nIntent Category: {latest_intent.intent_category}"
                            if latest_intent.recommended_action:
                                context_str += f"\nRecommended Action: {latest_intent.recommended_action}"
                            if latest_intent.signals:
                                context_str += f"\nSignals: {latest_intent.signals}"
                    break

            sales_agent = SalesConsultantAgent()
            system_instruction_text = sales_agent.get_system_instruction(context_str)
            tool_declarations = sales_agent.get_tool_declarations()

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
            
            # Setup Event Queue for pushing external Orchestrator events to Gemini
            voice_queue = get_voice_queue(session_id)
            
            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                logger.info("Connected to Gemini Live API")
                
                # Prompt the AI to speak first using a system instruction, rather than sending dummy audio.
                import time
                last_spoken_time = time.time()
                
                await session.send(
                    input="SYSTEM: The call has just connected. Speak first and greet the customer naturally based on their intent.", 
                    end_of_turn=True
                )
                
                SILENCE_THRESHOLD = getattr(settings, 'VOICE_SILENCE_RMS', 200)
                SILENCE_TIMEOUT_1 = getattr(settings, 'VOICE_SILENCE_TIMEOUT_1', 15.0)
                SILENCE_TIMEOUT_2 = getattr(settings, 'VOICE_SILENCE_TIMEOUT_2', 30.0)
                
                def get_rms(pcm_data: bytes) -> float:
                    count = len(pcm_data) // 2
                    if count == 0: return 0.0
                    try:
                        shorts = struct.unpack(f"<{count}h", pcm_data)
                        return math.sqrt(sum(s*s for s in shorts) / count)
                    except:
                        return 0.0
                
                async def send_to_gemini():
                    nonlocal last_spoken_time
                    try:
                        chunk_count = 0
                        while True:
                            data = await websocket.receive_bytes()
                            if not data:
                                break
                            
                            chunk_count += 1
                            if chunk_count % 100 == 0:
                                logger.info(f"Received {chunk_count} chunks from client, last rms={get_rms(data):.2f}")
                            
                            if chunk_count % 5 == 0:
                                rms = get_rms(data)
                                if rms > SILENCE_THRESHOLD:
                                    last_spoken_time = time.time()
                            
                            await session.send_realtime_input(
                                media=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                            )
                    except WebSocketDisconnect:
                        logger.info("Client WebSocket disconnected.")
                    except Exception as e:
                        logger.error(f"Error in send_to_gemini: {e}")
                        
                async def check_silence():
                    nonlocal last_spoken_time
                    prompt_1_sent = False
                    try:
                        while True:
                            await asyncio.sleep(1.0)
                            idle = time.time() - last_spoken_time
                            if idle > SILENCE_TIMEOUT_1 and not prompt_1_sent:
                                logger.info(f"User silent for {SILENCE_TIMEOUT_1}s. Sending check prompt.")
                                await session.send(
                                    input="SYSTEM: The user has been silent for 15 seconds. Please ask 'Are you still there?'",
                                    end_of_turn=True
                                )
                                prompt_1_sent = True
                            elif idle > SILENCE_TIMEOUT_2:
                                logger.info(f"User silent for {SILENCE_TIMEOUT_2}s. Terminating.")
                                await session.send(
                                    input="SYSTEM: The user has been silent for over 30 seconds. Please say a polite goodbye and use the end_conversation tool immediately.",
                                    end_of_turn=True
                                )
                                break
                            elif idle < SILENCE_TIMEOUT_1:
                                prompt_1_sent = False
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error in check_silence: {e}")

                async def receive_from_gemini():
                    while True:
                        try:
                            async for response in session.receive():
                                if response.server_content and response.server_content.model_turn and response.server_content.model_turn.parts:
                                    for part in response.server_content.model_turn.parts:
                                        if part.inline_data and part.inline_data.data is not None:
                                            await websocket.send_bytes(part.inline_data.data)
                                        elif part.text:
                                            logger.info(f"Gemini text: {part.text}")
                                
                                if response.tool_call:
                                    function_responses = []
                                    for call in response.tool_call.function_calls:
                                        name = call.name
                                        args = call.args or {}
                                        logger.info(f"Gemini requested tool: {name} with args {args}")
                                        
                                        from app.services.orchestrator.service import OrchestratorService
                                        orchestrator = OrchestratorService()
                                        
                                        try:
                                            result_data = {}
                                            if name == "request_product_recommendations":
                                                if session_id:
                                                    await orchestrator.handle_product_recommendation_requested(session_id, args)
                                                result_data = {"status": "queued", "message": "Product recommendations requested from Product Intelligence agent. Please wait, do not ask again."}
                                            
                                            elif name == "confirm_product_selection":
                                                if session_id:
                                                    await orchestrator.handle_product_confirmed(session_id, args.get("product_id"))
                                                result_data = {"status": "processing", "message": "Product selection confirmed. Commerce engine is adding to cart."}
                                                
                                            elif name == "end_conversation":
                                                if session_id:
                                                    await orchestrator.handle_customer_not_interested(session_id)
                                                result_data = {"status": "success", "message": "Conversation ended successfully."}
                                            
                                            else:
                                                result_data = {"status": "error", "message": f"Unknown tool {name}"}
                                            
                                            function_responses.append(
                                                types.FunctionResponse(
                                                    name=name,
                                                    id=call.id,
                                                    response=result_data
                                                )
                                            )
                                        except Exception as e:
                                            logger.error(f"Error executing tool {name}: {e}")
                                            function_responses.append(
                                                types.FunctionResponse(
                                                    name=name,
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
                            await asyncio.sleep(0.1)
                            
                async def listen_for_orchestrator_events():
                    try:
                        while True:
                            event = await voice_queue.get()
                            event_type = event.get("event_type")
                            data = event.get("data")
                            logger.info(f"Voice Session received internal event: {event_type}")
                            
                            if event_type == "PRODUCT_RECOMMENDATIONS_READY":
                                # Push to Gemini as a system text update
                                message = f"SYSTEM UPDATE: The product intelligence system has returned the following options for the user. Explain them naturally based on their needs:\n\n{json.dumps(data, indent=2)}"
                                await session.send(
                                    input=message,
                                    end_of_turn=True
                                )
                                
                            elif event_type == "COMMERCE_RESULT":
                                message = f"SYSTEM UPDATE: The commerce action returned: {json.dumps(data)}. If successful, confirm to the user and naturally close the conversation."
                                await session.send(
                                    input=message,
                                    end_of_turn=True
                                )
                                
                    except asyncio.CancelledError:
                        logger.info("listen_for_orchestrator_events task cancelled.")
                    except Exception as e:
                        logger.error(f"Error in listen_for_orchestrator_events: {e}")

                # Run tasks concurrently. If one finishes (like send_to_gemini on disconnect), cancel the rest.
                tasks = [
                    asyncio.create_task(send_to_gemini()),
                    asyncio.create_task(receive_from_gemini()),
                    asyncio.create_task(listen_for_orchestrator_events())
                ]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()

        except Exception as e:
            logger.error(f"Failed to handle Gemini Live session: {e}")
        finally:
            cleanup_voice_queue(session_id)
            
            # Notify Orchestrator that call ended
            try:
                orchestrator = OrchestratorService()
                # Run the async method in the background since we are inside a finally block of an async func
                # Wait, handle_session is an async function, we can just await it directly!
                await orchestrator.handle_call_disconnected(session_id)
            except Exception as e:
                logger.error(f"Failed to notify orchestrator of disconnect: {e}")

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
