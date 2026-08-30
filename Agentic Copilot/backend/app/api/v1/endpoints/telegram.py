from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Customer, CustomerSession
from app.graph.orchestrator import run_copilot_graph
from app.integrations.telegram.provider import get_telegram_provider
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()
telegram_provider = get_telegram_provider()

async def process_telegram_message_background(chat_id: str, text: str):
    # Retrieve customer by chat_id
    # If doesn't exist, maybe create a demo one or reject
    try:
        async for db in get_db():
            result = await db.execute(
                select(Customer).where(Customer.telegram_chat_id == str(chat_id))
            )
            customer = result.scalar_one_or_none()
            
            if not customer:
                logger.info(f"Received message from unknown Telegram user {chat_id}, linking to demo user")
                # For demo purposes, we can link them to the cust_demo user if they message us
                result = await db.execute(select(Customer).where(Customer.id == 'cust_demo'))
                customer = result.scalar_one_or_none()
                if customer:
                    customer.telegram_chat_id = str(chat_id)
                    await db.commit()
                    await telegram_provider.send_text(str(chat_id), "Welcome to the Razorpay Agentic Commerce demo! I'm your AI Sales Consultant.")
                else:
                    logger.error("Could not find cust_demo customer.")
                    return
            
            # Find their active session or create a new one
            result = await db.execute(
                select(CustomerSession)
                .where(CustomerSession.user_id == customer.id)
                .order_by(CustomerSession.created_at.desc())
                .limit(1)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                session_id = f"tg_sess_{uuid.uuid4().hex[:8]}"
                session = CustomerSession(session_id=session_id, user_id=customer.id)
                db.add(session)
                await db.commit()
            
            session_id = session.session_id
            
            # Now run the LangGraph orchestrator with this new message
            # For Telegram, we might bypass IntentAgent if it's a direct message, 
            # or just set a default state so it goes to SalesConsultant
            
            initial_state = {
                "session_id": session_id,
                "channel": "TELEGRAM",
                "telegram_chat_id": str(chat_id),
                "events": [],
                "intent_score": 1.0, # Direct message implies high intent
                "intent_category": "HIGH_PURCHASE_INTENT",
                "should_intervene": True,
                "latest_user_message": text,
                "chat_history": [] # TODO: Fetch chat history from DB
            }
            
            logger.info(f"Running LangGraph for Telegram user {chat_id} (session: {session_id})")
            
            # The sales consultant node in graph will respond, but we also need a way to 
            # actually send the message back to Telegram. We can modify the orchestrator 
            # to check the channel and use TelegramProvider.
            
            await run_copilot_graph(session_id, initial_state)
            break
            
    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}")

@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        update = await request.json()
        logger.info(f"Telegram Webhook received: {update}")
        
        # Simple message parsing
        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]
            
            # Process in background to return 200 OK to Telegram quickly
            background_tasks.add_task(process_telegram_message_background, chat_id, text)
            
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in Telegram webhook: {e}")
        return {"status": "error"}
