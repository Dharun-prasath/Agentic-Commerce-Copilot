from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.agents.commerce.prompts import COMMERCE_AGENT_SYSTEM_PROMPT
from app.integrations.demo_app.client import DemoCommerceClient
import logging
import json

from app.agents.config import get_agent_config

logger = logging.getLogger(__name__)

demo_client = DemoCommerceClient()

@tool
async def get_cart_status(session_id: str, token: Optional[str] = None) -> str:
    """Get the current cart contents for the user."""
    try:
        cart = await demo_client.get_cart(session_id, token)
        return json.dumps(cart)
    except Exception as e:
        return f"Error fetching cart: {str(e)}"

@tool
async def add_product_to_cart(session_id: str, product_id: str, quantity: int = 1, token: Optional[str] = None) -> str:
    """Add a product to the user's cart using its exact product_id."""
    try:
        cart = await demo_client.add_to_cart(session_id, product_id, quantity, token)
        return json.dumps(cart)
    except Exception as e:
        return f"Error adding to cart: {str(e)}"

class CommerceAgent:
    def __init__(self):
        model_name = settings.COMMERCE_AGENT_MODEL or settings.LLM_MODEL
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0
        )
        self.tools = [get_cart_status, add_product_to_cart]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
    async def process_commerce_intent(self, user_intent: str, session_id: str, token: Optional[str] = None) -> str:
        config = await get_agent_config("commerce")
        sys_prompt = config.get("system_prompt", COMMERCE_AGENT_SYSTEM_PROMPT)
        
        if config.get("temperature") is not None:
            live_llm = ChatGoogleGenerativeAI(
                model=config.get("model_name", settings.COMMERCE_AGENT_MODEL or settings.LLM_MODEL),
                google_api_key=settings.GEMINI_API_KEY,
                temperature=config.get("temperature", 0.0),
                top_p=config.get("top_p", 0.9),
                top_k=config.get("top_k", 40),
                max_output_tokens=config.get("max_output_tokens", 1024)
            )
            live_llm_with_tools = live_llm.bind_tools(self.tools)
        else:
            live_llm_with_tools = self.llm_with_tools

        system_prompt = f"{sys_prompt}\nSession ID: {session_id}\nToken provided: {'Yes' if token else 'No'}"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_intent)
        ]
        
        try:
            for _ in range(3):
                response = await self.llm_with_tools.ainvoke(messages)
                messages.append(response)
                
                if not response.tool_calls:
                    break
                    
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "get_cart_status":
                        # Manually inject session and token if needed, or rely on LLM if they use it
                        kwargs = tool_call["args"]
                        if "session_id" not in kwargs:
                            kwargs["session_id"] = session_id
                        if "token" not in kwargs:
                            kwargs["token"] = token
                        tool_msg = await get_cart_status.ainvoke(kwargs)
                    elif tool_call["name"] == "add_product_to_cart":
                        kwargs = tool_call["args"]
                        if "session_id" not in kwargs:
                            kwargs["session_id"] = session_id
                        if "token" not in kwargs:
                            kwargs["token"] = token
                        tool_msg = await add_product_to_cart.ainvoke(kwargs)
                    else:
                        tool_msg = AIMessage(content="Unknown tool")
                    messages.append(tool_msg)
            
            return messages[-1].content if isinstance(messages[-1], AIMessage) else "Unable to process commerce action."
        except Exception as e:
            logger.error(f"Error in Commerce Agent: {str(e)}")
            return "Commerce operations are currently unavailable."
