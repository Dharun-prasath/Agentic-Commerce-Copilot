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
        print(dir(session))
        print("Done")

asyncio.run(main())
