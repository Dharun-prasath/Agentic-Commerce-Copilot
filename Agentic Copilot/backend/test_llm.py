from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

class IntentOutput(BaseModel):
    intent_score: float = Field(description="Float between 0.0 and 1.0 (1.0 being ready to buy immediately)")
    intent_category: str = Field(description="One of HIGH_PURCHASE_INTENT, MEDIUM_INTENT, LOW_INTENT")
    confidence: float = Field(description="Float between 0.0 and 1.0")
    signals: list[str] = Field(description="A list of key observations from the events")
    recommended_action: str = Field(description="What the system should do, e.g. INITIATE_SALES_CONVERSATION, DO_NOTHING")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key="fake_key",
    temperature=0.0
)
print("LLM model:", llm.model)
try:
    structured_llm = llm.with_structured_output(IntentOutput)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
