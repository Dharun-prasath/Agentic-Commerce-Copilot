import logging
from typing import Dict, Any, List
from google.genai import types
from app.agents.sales_consultant.prompts import SALES_CONSULTANT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class SalesConsultantAgent:
    """
    Logical configuration and state management for the Sales Consultant Voice Agent.
    This class does NOT execute tools directly or manage the websocket; it provides 
    the schema and context for the VoiceProvider.
    """

    def get_system_instruction(self, context_str: str = "") -> str:
        instruction = SALES_CONSULTANT_SYSTEM_PROMPT
        if context_str:
            instruction += f"\n\nContext:\n{context_str}"
        return instruction

    def get_tool_declarations(self) -> types.Tool:
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="request_product_recommendations",
                    description="Request product options based on customer requirements. Call this when you have enough info.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "category": {"type": "STRING", "description": "Product category (e.g. laptop)"},
                            "budget_max": {"type": "INTEGER", "description": "Maximum budget in INR"},
                            "primary_use": {"type": "STRING", "description": "What they will use it for"},
                            "specific_requirements": {"type": "STRING", "description": "Other specs like RAM, GPU, etc."}
                        },
                        "required": ["category"]
                    }
                ),
                types.FunctionDeclaration(
                    name="confirm_product_selection",
                    description="Triggered ONLY when the customer explicitly agrees to purchase a specific product.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "product_id": {"type": "STRING", "description": "The ID of the confirmed product"}
                        },
                        "required": ["product_id"]
                    }
                ),
                types.FunctionDeclaration(
                    name="end_conversation",
                    description="Triggered when the customer explicitly rejects or wants to end the call (e.g. 'not interested').",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "reason": {"type": "STRING", "description": "Reason for ending, e.g. CUSTOMER_NOT_INTERESTED"}
                        },
                        "required": ["reason"]
                    }
                )
            ]
        )
