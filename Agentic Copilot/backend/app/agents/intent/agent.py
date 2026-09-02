from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.core.config import settings
from app.agents.intent.prompts import INTENT_AGENT_SYSTEM_PROMPT
import logging

from app.agents.config import get_agent_config
from app.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)

class IntentOutput(BaseModel):
    intent_score: float = Field(description="Float between 0.0 and 1.0 (1.0 being ready to buy immediately)")
    intent_category: str = Field(description="One of HIGH_PURCHASE_INTENT, MEDIUM_INTENT, LOW_INTENT")
    confidence: float = Field(description="Float between 0.0 and 1.0")
    signals: List[str] = Field(description="A list of key observations from the events")
    recommended_action: str = Field(description="What the system should do, e.g. INITIATE_SALES_CONVERSATION, DO_NOTHING")

class ProductOfInterest(BaseModel):
    product_id: str = Field(description="Internal UUID of the product")
    product_name: str = Field(description="Name of the product")
    category: str = Field(default="", description="Category of the product")
    price: float = Field(default=0.0, description="Price of the product")

class StructuredIntentOutput(BaseModel):
    intent_category: str = Field(description="e.g. HIGH_PURCHASE_INTENT, RESEARCHING, CASUAL_BROWSING")
    confidence: float = Field(description="Float between 0.0 and 1.0")
    customer_interest: str = Field(description="Specific description of what the customer is interested in")
    buying_stage: str = Field(description="e.g. AWARENESS, CONSIDERATION, DECISION")
    behaviour_summary: str = Field(description="Summary of the customer's shopping behaviour in this session. USE PRODUCT NAMES, NOT UUIDS.")
    products_of_interest: List[ProductOfInterest] = Field(description="Specific products the customer showed strong interest in")
    categories_of_interest: List[str] = Field(description="Categories the customer explored")
    reasoning: str = Field(description="Detailed reasoning for why this intent was determined based on the behavioral session summary")
    recommended_action: str = Field(description="What should be done next? e.g. CONTACT_CUSTOMER, DO_NOTHING")
    sales_consultant_context: str = Field(description="A structured string summary to be passed to a human or AI sales agent to help them jump right into the conversation.")

class IntentAgent:
    def __init__(self):
        model_name = settings.INTENT_AGENT_MODEL or settings.LLM_MODEL
        print(f"DEBUG: IntentAgent model_name is {model_name}")
        self.llm = get_llm(model_name=model_name)
        try:
            self.structured_llm = self.llm.with_structured_output(IntentOutput)
            self.structured_llm_new = self.llm.with_structured_output(StructuredIntentOutput)
            print("DEBUG: IntentAgent structured output initialized successfully")
        except Exception as e:
            print(f"DEBUG: IntentAgent failed to init structured output: {e}")
            raise
            
    async def analyze_intent_structured(self, structured_input: Dict[str, Any], session_id: str) -> StructuredIntentOutput:
        from app.core.telemetry import trace
        import time
        import json
        
        async with trace("n_intent_agent", "agent", session_id) as t:
            t.set_input(structured_input)
            t.add_event("Starting Intent Analysis")
            
            try:
                config = await get_agent_config("intent")
                # We use a dedicated prompt for the new structured reasoning
                sys_prompt = """You are the Intent Intelligence Engine.
You receive a structured summary of a customer's shopping session.
The session contains deterministic rule-based scores and behavioral signals.
Your job is to reason over this complete session and determine the true customer intent.
Do not blindly repeat the rule score. Differentiate between deep research and immediate purchase intent.
Output a structured JSON response containing your reasoning and the context for a future Sales Consultant.

CRITICAL INSTRUCTION FOR SPEED:
You are running locally. To ensure ultra-fast response times, KEEP ALL TEXT FIELDS (`behaviour_summary`, `reasoning`, `sales_consultant_context`) EXTREMELY SHORT (1 sentence maximum). Be direct and concise.

CRITICAL INSTRUCTION FOR DATA:
When writing `customer_interest`, `behaviour_summary`, `reasoning`, and `sales_consultant_context`, you MUST use the human-readable product names (e.g. "Dell XPS 15") and categories. NEVER output raw UUIDs in natural-language fields. The raw UUIDs should only be preserved in the `product_id` field of `products_of_interest`.
"""
                
                if config.get("temperature") is not None:
                    live_llm = get_llm(
                        model_name=config.get("model_name", settings.INTENT_AGENT_MODEL or settings.LLM_MODEL),
                        temperature=config.get("temperature", 0.0),
                        top_p=config.get("top_p", 0.9),
                        top_k=config.get("top_k", 40),
                        max_output_tokens=config.get("max_output_tokens", 1024)
                    )
                    structured_llm = live_llm.with_structured_output(StructuredIntentOutput)
                else:
                    structured_llm = self.structured_llm_new

                prompt = f"{sys_prompt}\n\nSession Summary:\n{json.dumps(structured_input, indent=2)}"
                
                t.add_event("Calling LLM for intent analysis")
                start_time = time.time()
                result = await structured_llm.ainvoke(prompt)
                end_time = time.time()
                
                t.add_tool_call("llm", "ainvoke", "structured_input", start_time, end_time, "SUCCESS", result.model_dump())
                t.set_output(result.model_dump())
                t.add_event(f"Intent detected: {result.intent_category} (confidence: {result.confidence})")
                
                return result
            except Exception as e:
                logger.error(f"Error in IntentAgent analysis: {e}")
                t.set_error(e)
                raise
        
    async def analyze_intent(self, events: List[Dict[str, Any]]) -> IntentOutput:
        try:
            config = await get_agent_config("intent")
            sys_prompt = config.get("system_prompt", INTENT_AGENT_SYSTEM_PROMPT)
            
            if config.get("temperature") is not None:
                live_llm = get_llm(
                    model_name=config.get("model_name", settings.INTENT_AGENT_MODEL or settings.LLM_MODEL),
                    temperature=config.get("temperature", 0.0),
                    top_p=config.get("top_p", 0.9),
                    top_k=config.get("top_k", 40),
                    max_output_tokens=config.get("max_output_tokens", 1024)
                )
                structured_llm = live_llm.with_structured_output(IntentOutput)
            else:
                structured_llm = self.structured_llm

            prompt = f"{sys_prompt}\n\nCustomer Events:\n{events}"
            result = await structured_llm.ainvoke(prompt)
            return result
        except Exception as e:
            logger.error(f"Error analyzing intent: {str(e)}")
            # Fallback output
            return IntentOutput(
                intent_score=0.0,
                intent_category="LOW_INTENT",
                confidence=0.0,
                signals=["Error in analysis"],
                recommended_action="DO_NOTHING"
            )
