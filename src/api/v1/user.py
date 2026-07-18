from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.builder import get_services
from src.dto.user import UserLoginRequest
from src.services.user import IUserService

router = APIRouter(prefix="/user")


def get_user_service():
    return get_services().user_service


UserServiceDep = Annotated[IUserService, Depends(get_user_service)]


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: UserLoginRequest, service: UserServiceDep):
    try:
        token = service.login(request)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
