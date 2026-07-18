from fastapi import APIRouter
from src.api.v1.user import router as user_router

router = APIRouter(prefix="/v1/api")


router.include_router(user_router)
