from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    realm: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    realm: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    attributes: Optional[dict[str, Any]] = None


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType")
    expires_at: str = Field(alias="expiresAt")
    roles: list[str]


class AuthorizeRequest(BaseModel):
    realm: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    action: str = Field(min_length=1)
    context: Optional[dict[str, Any]] = None


class AuthorizationDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed: bool
    matched_policies: list[str] = Field(alias="matchedPolicies")
