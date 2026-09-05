import json
import logging
from typing import List, Dict, Any, Optional
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


class LightweightProductRecommendation(BaseModel):
    product_id: str = Field(description="The EXACT id string provided in the retrieved products JSON (e.g., '1', '2'). Do NOT output a UUID or a product name.")
    match_score: Optional[float] = Field(default=0.8, description="A score from 0.0 to 1.0 indicating how well this matches the customer requirement")
    match_reason: Optional[str] = Field(default="", description="A short explanation of why this product is recommended")
    key_features: Optional[List[str]] = Field(default=[], description="List of 3-5 specific key specs/features pulled from the product specs")

class LightweightProductIntelligenceOutput(BaseModel):
    recommendations: List[LightweightProductRecommendation] = Field(default=[], description="List of recommended products")
    comparison_summary: Optional[str] = Field(default="", description="A summary comparing the top recommended products")
    recommendation_summary: Optional[str] = Field(default="", description="A friendly summary paragraph to send to the customer")


class ProductIntelligenceAgent:
    def __init__(self):
        model_name = settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL
        self.llm = get_llm(model_name=model_name)
        self.tools = [search_products, get_product_details]
        
    async def generate_recommendations(self, mock_requirement: Dict[str, Any], session_id: str) -> ProductIntelligenceOutput:
        """
        Takes a structured Mock Customer Requirement dict and returns structured Product Recommendations.
        """
        import time
        from app.core.telemetry import trace
        
        async with trace("n_product_intelligence", "agent", session_id) as t:
            t.set_input(mock_requirement)
            t.add_event("Starting product intelligence")
            
            config = await get_agent_config("product")
            sys_prompt = config.get("system_prompt", PRODUCT_INTELLIGENCE_SYSTEM_PROMPT)
            
            live_llm = get_llm(
                model_name=config.get("model_name", settings.PRODUCT_AGENT_MODEL or settings.LLM_MODEL),
                temperature=config.get("temperature", 0.0),
                top_p=config.get("top_p", 0.9),
                top_k=config.get("top_k", 40),
                max_output_tokens=config.get("max_output_tokens", 1024)
            )
            
            from langchain_core.output_parsers import JsonOutputParser
            parser = JsonOutputParser(pydantic_object=LightweightProductIntelligenceOutput)
            
            # PRE-FETCH: Do the search in code to avoid 3-4 round trips of LLM tool calling
            query_params = {}
            if mock_requirement.get("category"):
                cat_input = str(mock_requirement["category"]).lower()
                if "laptop" in cat_input:
                    query_params["category"] = "laptops"
                elif "accessor" in cat_input:
                    query_params["category"] = "accessories"
                else:
                    query_params["search"] = cat_input
                    
            if mock_requirement.get("brand"):
                query_params["brand"] = str(mock_requirement["brand"])
                
            if mock_requirement.get("budget_max"):
                try:
                    query_params["max_price"] = float(mock_requirement["budget_max"])
                except (ValueError, TypeError):
                    pass
                    
            query_params["page_size"] = 5 # Fetch top 5 candidates to make LLM generation ultrafast
            
            t.add_event(f"Querying catalog with params: {query_params}")
            search_results = {}
            try:
                search_start = time.time()
                search_results = await demo_client.get_products(query_params)
                search_end = time.time()
                t.add_tool_call("demo_client", "get_products", query_params, search_start, search_end, "SUCCESS", search_results)
                
                # Only give the LLM essential fields to read to save input tokens too!
                minimal_products = []
                idx_to_uuid = {}
                for idx, item in enumerate(search_results.get("items", [])):
                    idx_str = str(idx + 1)
                    idx_to_uuid[idx_str] = str(item.get("id"))
                    minimal_products.append({
                        "id": idx_str, # Use simple integer IDs to prevent LLMs from hallucinating UUIDs
                        "name": item.get("name"),
                        "price": item.get("price"),
                        "brand": item.get("brand"),
                        "description": item.get("description", "")[:200]
                    })
                products_json = json.dumps(minimal_products, indent=2)
                t.add_event(f"Found {len(search_results.get('items', []))} candidate products")
            except Exception as e:
                logger.error(f"PI Agent pre-search failed: {e}")
                products_json = "[]"
                idx_to_uuid = {}
                t.add_tool_call("demo_client", "get_products", query_params, time.time(), time.time(), "FAILED", error=str(e))
                t.add_event("Catalog catalog failed")
            
            messages = [
                SystemMessage(content=sys_prompt),
                HumanMessage(content=f"Please analyze these customer requirements:\n{json.dumps(mock_requirement, indent=2)}\n\nHere are the products retrieved from the catalog:\n{products_json}\n\nAct as the Product Intelligence Agent. Select the top 1-2 BEST matching products from the list. You MUST output ONLY valid JSON using the following schema:\n{parser.get_format_instructions()}")
            ]
            
            try:
                # SINGLE PASS: Directly output structured JSON
                t.add_event("Ranking and generating recommendations")
                start_time = time.time()
                llm_response = await live_llm.ainvoke(messages)
                structured_response = parser.invoke(llm_response)
                end_time = time.time()
                
                response_dict = structured_response

                
                t.add_tool_call("llm", "ainvoke", "mock_requirement", start_time, end_time, "SUCCESS", response_dict)
                
                logger.info(f"PI Agent finished in {end_time - start_time:.2f} seconds")
                t.add_event("Recommendations generated successfully")
                
                # EXACT DB DATA INJECTION: Overwrite LLM schema fields with actual DB fields
                db_items_map = {str(item["id"]): item for item in search_results.get("items", [])}
                
                full_recommendations = []
                # Post-process the response_dict into full ProductRecommendation models
                for rec in response_dict.get("recommendations", []):
                    prod_id_raw = str(rec.get("product_id"))
                    prod_id = idx_to_uuid.get(prod_id_raw, prod_id_raw) # map integer ID back to UUID
                    if prod_id in db_items_map:
                        db_item = db_items_map[prod_id]
                        cat_name = db_item.get("category", {}).get("name", "") if isinstance(db_item.get("category"), dict) else ""
                        
                        full_rec = ProductRecommendation(
                            product_id=prod_id,
                            product_name=db_item.get("name", ""),
                            product_slug=db_item.get("slug", ""),
                            brand=db_item.get("brand", ""),
                            product_url=f"/products/{db_item.get('slug', '')}",
                            image_url=db_item.get("thumbnail", "") or "",
                            price=float(db_item.get("price") or 0.0),
                            original_price=float(db_item.get("original_price") or 0.0),
                            rating=float(db_item.get("rating") or 0.0),
                            review_count=int(db_item.get("review_count") or 0),
                            match_score=rec.get("match_score", 0.0),
                            match_reason=rec.get("match_reason", ""),
                            key_features=rec.get("key_features", []),
                            category=cat_name
                        )
                        full_recommendations.append(full_rec)
                            
                final_output = ProductIntelligenceOutput(
                    schema_version="1.0",
                    recommendations=full_recommendations,
                    comparison_summary=response_dict.get("comparison_summary", ""),
                    recommendation_summary=response_dict.get("recommendation_summary", "")
                )
                
                t.set_output(final_output.model_dump())
                return final_output
                
            except Exception as e:
                logger.error(f"Error in Product Intelligence Agent generating recommendations: {str(e)}")
                t.set_error(e)
                # Return empty structured result as fallback
                fallback = ProductIntelligenceOutput(
                    recommendations=[],
                    comparison_summary="An error occurred while fetching products.",
                    recommendation_summary="Sorry, I couldn't find any recommendations at this moment."
                )
                t.set_output(fallback.model_dump())
                return fallback
