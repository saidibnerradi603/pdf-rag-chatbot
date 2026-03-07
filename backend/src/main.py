from fastapi import FastAPI, status
from src.api.v1.router import api_router
from src.core.config import settings
from fastapi.middleware.cors import CORSMiddleware


import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
 

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Retrieval-Augmented Generation system for intelligent question answering over PDF documents",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BACKEND_CORS_ORIGIN],          
    allow_credentials=True,
    allow_methods=["*"],           
    allow_headers=["*"],          
)


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get(
    "/health",
    summary="Health Check",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    },
    


@app.get(
    "/",
    summary="Root Endpoint",
    status_code=status.HTTP_200_OK,
)
async def root():
    return (
        {
            "message": f"Welcome to {settings.APP_NAME}",
            "docs": "/docs",
            "redoc": "/redoc",
            "api_prefix": settings.API_V1_PREFIX,
        },
    )
 