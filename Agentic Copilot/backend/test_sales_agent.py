import asyncio
from app.core.config import settings
from google import genai
from google.genai import types
from app.agents.sales_consultant.prompts import SALES_CONSULTANT_SYSTEM_PROMPT
import json

async def main():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    mock_data = {
      "schema_version": "1.0",
      "recommendations": [
        {
          "product_id": "bb362054-bbb4-4381-b483-4fbc9603e801",
          "product_name": "XPS 16 - Core Ultra 9 / 64GB / 2TB",
          "price": 150000.0,
          "match_reason": "high performance for development",
          "key_features": []
        }
      ],
      "recommendation_summary": "I found 1 product."
    }
    
    # We will test using the text-based generate_content to see what it wants to say
    # since testing voice output is hard in a script without saving audio.
    # We just want to see if the model UNDERSTANDS the system update.
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(role="user", parts=[
                types.Part.from_text(text="I am looking for a laptop.")
            ]),
            types.Content(role="model", parts=[
                types.Part.from_tool_call(
                    types.FunctionCall(name="request_product_recommendations", args={})
                )
            ]),
            types.Content(role="user", parts=[
                types.Part.from_tool_response(
                    types.FunctionResponse(name="request_product_recommendations", response={"status": "processing"})
                )
            ]),
            types.Content(role="model", parts=[
                types.Part.from_text(text="Got it, let me check our catalog real quick...")
            ]),
            types.Content(role="user", parts=[
                types.Part.from_text(text=f"SYSTEM UPDATE: The product intelligence system has returned the following options for the user. Explain them naturally based on their needs:\n\n{json.dumps(mock_data)}")
            ])
        ],
        config=types.GenerateContentConfig(
            system_instruction=SALES_CONSULTANT_SYSTEM_PROMPT,
            temperature=0.7
        )
    )
    
    print("AGENT SAYS:", response.text)

if __name__ == "__main__":
    asyncio.run(main())
