from supabase import acreate_client,AsyncClient
from llama_cloud import AsyncLlamaCloud
from src.core.config import settings
from langchain_cohere import CohereEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel 



_supabase: AsyncClient | None = None

async def get_supabase_client() -> AsyncClient:
    global _supabase
    if _supabase is None:
        _supabase = await acreate_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY.get_secret_value()
        )
    return _supabase



    

def get_llama_parse_client() -> AsyncLlamaCloud:
    return AsyncLlamaCloud(api_key=settings.LLAMA_CLOUD_API_KEY.get_secret_value())



def get_cohere_embeddings() -> CohereEmbeddings:
    return CohereEmbeddings(cohere_api_key=settings.COHERE_API_KEY.get_secret_value(),model="embed-english-v3.0")


# Centralized factory - easy switching between LLMs (gemini ↔ gpt ↔ claude ...) 
def get_chat_model() -> BaseChatModel:
    return init_chat_model(
        model="gemini-3.8-flash",
        model_provider="google_genai",
        temperature=0.2,
        streaming=True,
        google_api_key=settings.GOOGLE_API_KEY.get_secret_value()
    )
    

