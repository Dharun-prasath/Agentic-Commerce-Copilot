from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.agents.intent.agent import IntentAgent
from app.agents.product_intelligence.agent import ProductIntelligenceAgent
from app.agents.sales_consultant.agent import SalesConsultantAgent
from app.agents.commerce.agent import CommerceAgent
import logging

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    session_id: str
    channel: Optional[str] # e.g. "TELEGRAM", "ELECTRON"
    events: List[Dict[str, Any]]
    intent_score: Optional[float]
    intent_category: Optional[str]
    should_intervene: bool
    chat_history: List[Any]
    latest_user_message: Optional[str]
    latest_agent_response: Optional[str]
    commerce_action_result: Optional[str]
    telegram_chat_id: Optional[str]

intent_agent = IntentAgent()
product_agent = ProductIntelligenceAgent()
sales_agent = SalesConsultantAgent()
commerce_agent = CommerceAgent()

async def analyze_intent_node(state: GraphState) -> GraphState:
    logger.info(f"Analyzing intent for session {state['session_id']}")
    
    # If channel is telegram, always intervene
    if state.get("channel") == "TELEGRAM":
        return {
            **state,
            "intent_score": 1.0,
            "intent_category": "HIGH_PURCHASE_INTENT",
            "should_intervene": True
        }
        
    result = await intent_agent.analyze_intent(state["events"])
    
    # Save intent assessment to database
    from app.core.database import async_session_maker
    from app.models.models import IntentAssessment
    import uuid
    try:
        async with async_session_maker() as db:
            intent = IntentAssessment(
                id=str(uuid.uuid4()),
                session_id=state["session_id"],
                intent_score=result.intent_score,
                intent_category=result.intent_category,
                confidence=result.confidence,
                signals=result.signals,
                recommended_action=result.recommended_action
            )
            db.add(intent)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to save IntentAssessment: {e}")

    return {
        **state,
        "intent_score": result.intent_score,
        "intent_category": result.intent_category,
        "should_intervene": result.intent_category == "HIGH_PURCHASE_INTENT"
    }

import httpx
from app.integrations.telegram.provider import get_telegram_provider

async def sales_consultant_node(state: GraphState) -> GraphState:
    logger.info(f"Sales consultant processing for session {state['session_id']}")
    channel = state.get("channel", "ELECTRON")
    
    msg = state.get("latest_user_message", "Hello")
    response = await sales_agent.chat(msg, state.get("chat_history", []), session_id=state["session_id"])
    
    if channel == "ELECTRON":
        # Trigger Electron incoming call UI
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://127.0.0.1:3456/simulate", json={"session_id": state["session_id"]})
        except Exception as e:
            logger.error(f"Failed to trigger Electron app: {e}")
    elif channel == "TELEGRAM":
        chat_id = state.get("telegram_chat_id")
        if chat_id:
            provider = get_telegram_provider()
            await provider.send_text(chat_id, response)
            
    return {
        **state,
        "latest_agent_response": response
    }

def should_intervene_condition(state: GraphState) -> str:
    if state.get("should_intervene", False):
        return "sales_consultant"
    return "end"

from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def build_graph() -> StateGraph:
    workflow = StateGraph(GraphState)
    
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("sales_consultant", sales_consultant_node)
    
    workflow.set_entry_point("analyze_intent")
    
    workflow.add_conditional_edges(
        "analyze_intent",
        should_intervene_condition,
        {
            "sales_consultant": "sales_consultant",
            "end": END
        }
    )
    
    workflow.add_edge("sales_consultant", END)
    
    return workflow

async def run_copilot_graph(session_id: str, initial_state: dict):
    workflow = build_graph()
    
    # psycopg requires standard postgresql:// scheme
    db_url = settings.COPILOT_DATABASE_URL.replace("+asyncpg", "")
    
    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
        await checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": session_id}}
        return await app.ainvoke(initial_state, config=config)
