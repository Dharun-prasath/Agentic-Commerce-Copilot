import asyncio
from app.core.config import settings
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model = "gemini-2.5-flash-native-audio-latest"
    
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(parts=[types.Part.from_text(text="You are a helpful assistant.")]),
    )
    
    async with client.aio.live.connect(model=model, config=config) as session:
        print("Connected. Sending text update...")
        await session.send(input="SYSTEM UPDATE: Tell me a joke about a laptop.", end_of_turn=True)
        
        print("Waiting for response...")
        async for response in session.receive():
            if response.server_content and response.server_content.model_turn:
                print("Received model response turn!")
                break
            
if __name__ == "__main__":
    asyncio.run(main())
