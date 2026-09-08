from fastapi import APIRouter
from src.api.v1.client import router as client_router
from src.api.v1.oauth import router as oauth_router
from src.api.v1.user import router as user_router

router = APIRouter(prefix="/v1/api")


router.include_router(user_router)
router.include_router(oauth_router)
router.include_router(client_router)
