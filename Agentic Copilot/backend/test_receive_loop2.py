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
            turns=[types.Content(parts=[types.Part.from_text(text="Hi")])],
            turn_complete=True
        )
        await session.send(input=content)
        
        # turn 1
        async for response in session.receive():
            pass
        print("session.receive() exited first time.")
        
        # send another turn
        await session.send(input=types.LiveClientContent(turns=[types.Content(parts=[types.Part.from_text(text="How are you?")])], turn_complete=True))
        
        # turn 2
        async for response in session.receive():
            pass
        print("session.receive() exited second time.")

asyncio.run(main())
