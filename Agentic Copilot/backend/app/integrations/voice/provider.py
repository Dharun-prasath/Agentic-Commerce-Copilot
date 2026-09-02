from abc import ABC, abstractmethod
from typing import AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings
import logging
import asyncio
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Keep strong references to background tasks to prevent garbage collection
_bg_tasks = set()

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
        # User explicitly requested to use this model for the sales agent
        self.model = "models/gemini-2.5-flash-native-audio-preview-12-2025"
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
                
                # Prompt the AI to speak first using the actual context
                greeting_prompt = "SYSTEM: The call has just connected. Speak first. "
                if context_str:
                    greeting_prompt += f"Use the following context to greet the customer naturally and check if they are still interested:\n{context_str}"
                else:
                    greeting_prompt += "Greet the customer naturally."
                
                await session.send(
                    input=greeting_prompt, 
                    end_of_turn=True
                )
                
                async def send_to_gemini():
                    try:
                        while True:
                            data = await websocket.receive_bytes()
                            if not data:
                                break
                            
                            await session.send_realtime_input(
                                media=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                            )
                    except WebSocketDisconnect:
                        logger.info("Client WebSocket disconnected.")
                    except Exception as e:
                        logger.error(f"Error in send_to_gemini: {e}")

                async def receive_from_gemini():
                    global _bg_tasks
                    while True:
                        try:
                            async for response in session.receive():
                                if response.server_content:
                                    if getattr(response.server_content, 'interrupted', False):
                                        logger.info("Gemini interrupted, sending clear signal to frontend")
                                        import json
                                        await websocket.send_text(json.dumps({"action": "clear"}))
                                        
                                    if response.server_content.model_turn and response.server_content.model_turn.parts:
                                        for part in response.server_content.model_turn.parts:
                                            if part.inline_data and part.inline_data.data is not None:
                                                await websocket.send_bytes(part.inline_data.data)
                                            elif part.text:
                                                logger.info(f"Gemini text: {part.text}")
                                
                                if response.tool_call:
                                    function_responses = []
                                    for call in response.tool_call.function_calls or []:
                                        name = call.name
                                        
                                        # Safely convert protobuf MapComposite to a standard Python dictionary
                                        def proto_to_dict(obj):
                                            if hasattr(obj, 'items'):
                                                return {k: proto_to_dict(v) for k, v in obj.items()}
                                            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                                                return [proto_to_dict(x) for x in obj]
                                            return obj
                                            
                                        args = proto_to_dict(call.args) if call.args else {}
                                        logger.info(f"Gemini requested tool: {name} with args {args}")
                                        
                                        from app.services.orchestrator.service import OrchestratorService
                                        orchestrator = OrchestratorService()
                                        
                                        try:
                                            result_data = {}
                                            if name == "request_product_recommendations":
                                                if session_id:
                                                    # Run PI asynchronously so voice is not blocked
                                                    # Keep a strong reference to prevent GC from killing the task
                                                    task = asyncio.create_task(orchestrator.handle_product_recommendation_requested(session_id, args))
                                                    _bg_tasks.add(task)
                                                    task.add_done_callback(_bg_tasks.discard)
                                                    result_data = {"status": "processing", "message": "Query sent to Product Intelligence. It will notify you when ready. Tell the customer you are checking."}
                                                else:
                                                    result_data = {"status": "error", "message": "No session ID"}
                                            
                                            elif name == "confirm_product_selection":
                                                product_id = args.get("product_id")
                                                if session_id and product_id is not None:
                                                    task = asyncio.create_task(orchestrator.handle_product_confirmed(session_id, str(product_id)))
                                                    _bg_tasks.add(task)
                                                    task.add_done_callback(_bg_tasks.discard)
                                                result_data = {"status": "processing", "message": "Product selection confirmed. Commerce engine is adding to cart. Wait for the COMMERCE_RESULT system update before ending the call."}
                                                
                                            elif name == "end_conversation":
                                                reason = args.get("reason", "CUSTOMER_NOT_INTERESTED")
                                                if session_id:
                                                    if reason == "ADDED_TO_CART":
                                                        await orchestrator.handle_product_added_to_cart(session_id)
                                                    else:
                                                        await orchestrator.handle_customer_not_interested(session_id)
                                                result_data = {"status": "success", "message": "Conversation ended successfully."}
                                                
                                                # Schedule delayed connection drop to allow goodbye audio to stream
                                                async def delayed_close():
                                                    await asyncio.sleep(4)
                                                    try:
                                                        await websocket.close()
                                                    except:
                                                        pass
                                                asyncio.create_task(delayed_close())
                                            
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
                                # Extract essential info for the voice agent to prevent token overload
                                recs = data.get("recommendations", [])
                                simplified_recs = []
                                for r in recs:
                                    simplified_recs.append({
                                        "product_id": r.get("product_id"),
                                        "name": r.get("product_name"),
                                        "price": f"₹{r.get('price', 0)}",
                                        "why_it_matches": r.get("match_reason")
                                    })
                                
                                # Push to Gemini as a system text update
                                message = f"SYSTEM UPDATE: Product recommendations are ready. SPEAK NOW and explain these options to the customer conversationally (keep it brief):\n\n{json.dumps(simplified_recs, indent=2)}"
                                await session.send(
                                    input=message,
                                    end_of_turn=True
                                )
                                
                            elif event_type == "COMMERCE_RESULT":
                                message = f"SYSTEM UPDATE: The commerce action returned: {json.dumps(data)}. If successful, IMMEDIATELY say a polite goodbye and call end_conversation with reason ADDED_TO_CART."
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
