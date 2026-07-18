from typing import Optional, Union

from pydantic import BaseModel


class BootstrapUser(BaseModel):
    email: str
    password: str
    is_admin: bool = True
    is_active: bool = True

    class Config:
        orm_mode = True


class UserCreateRequestDto(BootstrapUser):
    email: str
    password: str
    first_name: Optional[str] | Union[str, None] = None
    last_name: Optional[str] | Union[str, None] = None
    is_admin: bool = False
    is_active: bool = True


class UserLoginRequest(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True
