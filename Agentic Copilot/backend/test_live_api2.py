import asyncio
from google import genai
from google.genai import types
from app.core.config import settings

async def main():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(parts=[types.Part.from_text(text="You are a helpful AI Voice Assistant. Keep your responses short.")])
    )
    async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
        print("Connected.")
        await session.send(input="Hello! The user has just connected to the call. Please say a short greeting to start the conversation.")
        print("Sent init message. Waiting for response...")
        async for response in session.receive():
            if response.server_content and response.server_content.model_turn:
                print("Received model turn response part.")
                break

asyncio.run(main())
