from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["Health"])
async def health_status():
    return {"message": "Research Agent API is running"}