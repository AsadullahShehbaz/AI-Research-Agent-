from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(title='Research Agent API',
    description='AI-powered research assistant using LangGraph',
    version='1.0.0')

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}