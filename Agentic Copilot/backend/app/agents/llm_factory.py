from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from app.core.config import settings

def get_llm(model_name: str, temperature: float = 0.0, top_p: float = 0.9, top_k: int = 40, max_output_tokens: int = 1024, **kwargs):
    """
    Instantiates the correct LangChain chat model based on the model_name.
    If the model name starts with 'gemini', it uses Google's Generative AI.
    Otherwise, it assumes it's a local model and uses Ollama.
    """
    if model_name.startswith("gemini"):
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
            **kwargs
        )
    else:
        # For Ollama models like 'gemma3:1b', 'llama3.1:8b'
        return ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=temperature,
            num_predict=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
            **kwargs
        )
