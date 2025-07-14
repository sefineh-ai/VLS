from fastapi import APIRouter
from app.api import auth, stream, chat_ws

router = APIRouter()
router.include_router(auth.router)
router.include_router(stream.router)
router.include_router(chat_ws.router)
