import asyncio
from google import genai
from google.genai import types
from app.core.config import settings

async def main():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO]
    )
    async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
        print("Connected.")
        content = types.LiveClientContent(
            turns=[types.Content(parts=[types.Part.from_text(text="Hi, start the conversation.")])],
            turn_complete=True
        )
        await session.send(input=content)
        print("Sent client content. Waiting...")
        async for response in session.receive():
            if response.server_content and response.server_content.model_turn:
                print("Received model turn response part.")
                break

asyncio.run(main())
