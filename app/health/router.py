from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "AgriCure Backend",
        "timestamp": datetime.utcnow().isoformat()
    }
