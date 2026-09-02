import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

from app.core.config import settings
from app.agents.product_intelligence.prompts import PRODUCT_INTELLIGENCE_SYSTEM_PROMPT
from app.integrations.demo_app.client import DemoCommerceClient
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

# Structured Output Schema
class ProductRecommendation(BaseModel):
    product_id: str = Field(description="The unique identifier (UUID) of the product")
    product_name: str = Field(description="The human-readable name of the product")
    product_slug: str = Field(description="The URL slug of the product (e.g. 'dell-xps-16-core-ultra-9---64gb---2tb')")
    brand: str = Field(default="", description="The brand/manufacturer of the product")
    product_url: str = Field(description="The frontend URL for the product: http://localhost:5174/products/{slug}")
    image_url: str = Field(default="", description="The relative URL of the product image (e.g. '/images/products/dell_xps.png')")
    price: float = Field(description="The current sale price of the product")
    original_price: float = Field(default=0.0, description="The original price before discount")
    rating: float = Field(default=0.0, description="The product rating out of 5")
    review_count: int = Field(default=0, description="Number of reviews")
    match_score: float = Field(description="A score from 0.0 to 1.0 indicating how well this matches the customer requirement")
    match_reason: str = Field(description="A short explanation of why this product is recommended")
    key_features: List[str] = Field(description="List of 3-5 specific key specs/features pulled from the product specs (e.g. 'Core Ultra 9 Processor', '64GB DDR5 RAM')")
    category: str = Field(default="", description="Product category name")

class ProductIntelligenceOutput(BaseModel):
    schema_version: str = Field(default="1.0")
    recommendations: List[ProductRecommendation] = Field(description="List of recommended products")
    comparison_summary: str = Field(description="A summary comparing the top recommended products")
    recommendation_summary: str = Field(description="A friendly summary paragraph to send to the customer")


class ProductIntelligenceAgent:
    def __init__(self):
        model_name = settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL
        self.llm = get_llm(model_name=model_name)
        self.tools = [search_products, get_product_details]
        
    async def generate_recommendations(self, mock_requirement: Dict[str, Any]) -> ProductIntelligenceOutput:
        """
        Takes a structured Mock Customer Requirement dict and returns structured Product Recommendations.
        """
        import time
        config = await get_agent_config("product")
        sys_prompt = config.get("system_prompt", PRODUCT_INTELLIGENCE_SYSTEM_PROMPT)
        
        live_llm = get_llm(
            model_name=config.get("model_name", settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL),
            temperature=config.get("temperature", 0.0),
            top_p=config.get("top_p", 0.9),
            top_k=config.get("top_k", 40),
            max_output_tokens=config.get("max_output_tokens", 2048)
        )
        
        # Structured output binding for final step
        llm_with_structured = live_llm.with_structured_output(ProductIntelligenceOutput)
        
        # PRE-FETCH: Do the search in code to avoid 3-4 round trips of LLM tool calling (saves 5+ seconds)
        query_parts = []
        if mock_requirement.get("category"):
            query_parts.append(str(mock_requirement["category"]))
        if mock_requirement.get("brand"):
            query_parts.append(str(mock_requirement["brand"]))
            
        query = " ".join(query_parts) if query_parts else "popular"
        
        try:
            search_results = await demo_client.search_products_autocomplete(query)
            products_json = json.dumps(search_results.get("products", []), indent=2)
        except Exception as e:
            logger.error(f"PI Agent pre-search failed: {e}")
            products_json = "[]"
        
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Please analyze these customer requirements:\n{json.dumps(mock_requirement, indent=2)}\n\nHere are the products retrieved from the catalog:\n{products_json}\n\nAct as the Product Intelligence Agent and output the structured JSON recommendations.")
        ]
        
        try:
            # SINGLE PASS: Directly output structured JSON
            start_time = time.time()
            structured_response = await llm_with_structured.ainvoke(messages)
            logger.info(f"PI Agent finished in {time.time() - start_time:.2f} seconds")
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in Product Intelligence Agent generating recommendations: {str(e)}")
            # Return empty structured result as fallback
            return ProductIntelligenceOutput(
                recommendations=[],
                comparison_summary="An error occurred while fetching products.",
                recommendation_summary="Sorry, I couldn't find any recommendations at this moment."
            )
