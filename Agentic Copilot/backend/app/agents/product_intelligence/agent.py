from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from typing import List, Dict, Any
from app.core.config import settings
from app.agents.product_intelligence.prompts import PRODUCT_INTELLIGENCE_SYSTEM_PROMPT
from app.integrations.demo_app.client import DemoCommerceClient
import logging
import json

from app.agents.config import get_agent_config
from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)

# Tools for the LLM
demo_client = DemoCommerceClient()

@tool
async def search_products(query: str) -> str:
    """Search for products using autocomplete and return a list of matches."""
    try:
        results = await demo_client.search_products_autocomplete(query)
        return json.dumps(results.get("products", []))
    except Exception as e:
        return f"Error searching products: {str(e)}"

@tool
async def get_product_details(slug: str) -> str:
    """Get full details and specifications for a specific product by its slug."""
    try:
        result = await demo_client.get_product(slug)
        return json.dumps(result)
    except Exception as e:
        return f"Error retrieving product details: {str(e)}"

class ProductIntelligenceAgent:
    def __init__(self):
        model_name = settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL
        self.llm = get_llm(model_name=model_name)
        self.tools = [search_products, get_product_details]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
    async def analyze_query(self, query: str) -> str:
        config = await get_agent_config("product")
        sys_prompt = config.get("system_prompt", PRODUCT_INTELLIGENCE_SYSTEM_PROMPT)
        
        if config.get("temperature") is not None:
            live_llm = get_llm(
                model_name=config.get("model_name", settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL),
                temperature=config.get("temperature", 0.0),
                top_p=config.get("top_p", 0.9),
                top_k=config.get("top_k", 40),
                max_output_tokens=config.get("max_output_tokens", 1024)
            )
            live_llm_with_tools = live_llm.bind_tools(self.tools)
        else:
            live_llm_with_tools = self.llm_with_tools

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=query)
        ]
        
        try:
            # We will just do a simple tool execution loop for now (max 3 iterations)
            for _ in range(3):
                response = await self.llm_with_tools.ainvoke(messages)
                messages.append(response)
                
                if not response.tool_calls:
                    break
                    
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "search_products":
                        tool_msg = await search_products.ainvoke(tool_call)
                    elif tool_call["name"] == "get_product_details":
                        tool_msg = await get_product_details.ainvoke(tool_call)
                    else:
                        tool_msg = AIMessage(content="Unknown tool")
                    messages.append(tool_msg)
            
            # The final response should be in the last AIMessage
            return messages[-1].content if isinstance(messages[-1], AIMessage) else "Unable to formulate answer."
        except Exception as e:
            logger.error(f"Error in Product Intelligence Agent: {str(e)}")
            return "I'm having trouble accessing the product catalog right now."
