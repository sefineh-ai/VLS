from fastapi import APIRouter
from app.api import auth, stream

router = APIRouter()
router.include_router(auth.router)
router.include_router(stream.router)
