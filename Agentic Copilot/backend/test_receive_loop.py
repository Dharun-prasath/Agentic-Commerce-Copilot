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
        async def receive_task():
            while True:
                try:
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            print("Received part.")
                    print("session.receive() exited!")
                except Exception as e:
                    print(f"receive loop exception: {e}")
                    break

        import asyncio
        asyncio.create_task(receive_task())
        
        content = types.LiveClientContent(
            turns=[types.Content(parts=[types.Part.from_text(text="Hi")])],
            turn_complete=True
        )
        print("Sending first content")
        await session.send(input=content)
        await asyncio.sleep(5)
        
        print("Sending second content")
        content2 = types.LiveClientContent(
            turns=[types.Content(parts=[types.Part.from_text(text="Are you there?")])],
            turn_complete=True
        )
        await session.send(input=content2)
        await asyncio.sleep(5)

asyncio.run(main())
