from fastapi import APIRouter
from src.api.v1.client import router as client_router
from src.api.v1.oauth import router as oauth_router
from src.api.v1.user import router as user_router
from src.api.v1.admin import router as admin_router
from src.api.v1.discovery import router as discovery_router

router = APIRouter(prefix="/v1/api")


router.include_router(user_router)
router.include_router(oauth_router)
router.include_router(client_router)
router.include_router(admin_router)
router.include_router(discovery_router)
