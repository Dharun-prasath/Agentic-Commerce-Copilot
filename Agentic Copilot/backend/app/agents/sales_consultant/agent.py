from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.agents.sales_consultant.prompts import SALES_CONSULTANT_SYSTEM_PROMPT
from app.agents.product_intelligence.agent import search_products, get_product_details
from app.agents.commerce.agent import get_cart_status, add_product_to_cart
import logging

from app.agents.config import get_agent_config
from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)

class SalesConsultantAgent:
    def __init__(self):
        # We will override these per request in chat() if config exists
        model_name = settings.SALES_AGENT_MODEL or settings.LLM_MODEL
        self.llm = get_llm(model_name=model_name, temperature=0.7)
        self.tools = [search_products, get_product_details, get_cart_status, add_product_to_cart]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
    async def chat(self, user_message: str, history: Optional[List[BaseMessage]] = None, session_id: str = "") -> str:
        if history is None:
            history = []
            
        config = await get_agent_config("sales")
        sys_prompt = config.get("system_prompt", SALES_CONSULTANT_SYSTEM_PROMPT)
        
        # Apply context memory limit (each turn is roughly 1 user message + 1 agent message)
        mem_limit = config.get("context_memory_size", 10) * 2
        if mem_limit > 0 and len(history) > mem_limit:
            history = history[-mem_limit:]
            
        # Optional: override llm params here if needed by re-instantiating or updating params
        if config.get("temperature") is not None:
            # Recreate LLM with live config for this request
            live_llm = get_llm(
                model_name=config.get("model_name", settings.SALES_AGENT_MODEL or settings.LLM_MODEL),
                temperature=config.get("temperature", 0.7),
                top_p=config.get("top_p", 0.9),
                top_k=config.get("top_k", 40),
                max_output_tokens=config.get("max_output_tokens", 1024)
            )
            live_llm_with_tools = live_llm.bind_tools(self.tools)
        else:
            live_llm_with_tools = self.llm_with_tools
            
        messages = [SystemMessage(content=f"{sys_prompt}\nSession ID: {session_id}")] + history + [HumanMessage(content=user_message)]
        
        try:
            # Simple tool execution loop (max 3)
            for _ in range(3):
                response = await self.llm_with_tools.ainvoke(messages)
                messages.append(response)
                
                if not response.tool_calls:
                    break
                    
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    if tool_name in ["get_cart_status", "add_product_to_cart"] and "session_id" not in tool_call["args"]:
                        tool_call["args"]["session_id"] = session_id

                    if tool_name == "search_products":
                        tool_msg = await search_products.ainvoke(tool_call)
                    elif tool_name == "get_product_details":
                        tool_msg = await get_product_details.ainvoke(tool_call)
                    elif tool_name == "get_cart_status":
                        tool_msg = await get_cart_status.ainvoke(tool_call)
                    elif tool_name == "add_product_to_cart":
                        tool_msg = await add_product_to_cart.ainvoke(tool_call)
                    else:
                        tool_msg = AIMessage(content="Unknown tool")
                    messages.append(tool_msg)
            
            return messages[-1].content if isinstance(messages[-1], AIMessage) else "Unable to process request."
        except Exception as e:
            logger.error(f"Error in Sales Consultant Agent: {str(e)}")
            return "I'm having some trouble connecting right now, but I'd love to help you find the right product."
