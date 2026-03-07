from src.api.v1.endpoints import document,auth,parse,chunk,embed,process,retrieve,chat
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(parse.router, prefix="/documents", tags=["Processing"])
api_router.include_router(chunk.router, prefix="/documents", tags=["Processing"])
api_router.include_router(embed.router, prefix="/documents", tags=["Processing"])
api_router.include_router(process.router, prefix="/documents", tags=["Processing"])
api_router.include_router(retrieve.router, prefix="/documents", tags=["Retrieval"])
api_router.include_router(chat.router, prefix="/conversations", tags=["Conversations"])  
