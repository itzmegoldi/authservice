from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.user import AdminClaimsDep
from src.builder import get_services
from src.dto.client import ClientCreateRequest, ClientRoleCreateRequest
from src.services.client import IClientService


router = APIRouter(prefix="/clients", tags=["clients"])


def get_client_service():
    return get_services().client_service


ClientServiceDep = Annotated[IClientService, Depends(get_client_service)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_client(
    request: ClientCreateRequest,
    service: ClientServiceDep,
    _: AdminClaimsDep,
):
    try:
        service.create_client(request)
        return {
            "client_id": request.client_id,
            "name": request.name,
            "realm": request.realm,
            "attributes": request.attributes,
            "allowed_grant_types": request.allowed_grant_types,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/{client_id}/roles", status_code=status.HTTP_201_CREATED)
async def create_client_role(
    client_id: str,
    request: ClientRoleCreateRequest,
    service: ClientServiceDep,
    _: AdminClaimsDep,
):
    try:
        service.create_role(client_id, request)
        return {
            "client_id": client_id,
            "name": request.name,
            "attributes": request.attributes,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/{client_id}/users/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_client_role(
    client_id: str,
    user_id: int,
    role_name: str,
    service: ClientServiceDep,
    _: AdminClaimsDep,
):
    try:
        service.assign_role(client_id, user_id, role_name)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
