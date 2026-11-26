from pydantic import BaseModel, Field


class ClientCreateRequest(BaseModel):
    client_id: str
    client_secret: str
    name: str
    realm: str
    attributes: dict = Field(default_factory=dict)
    allowed_grant_types: list[str] = Field(
        default_factory=lambda: ["password", "refresh_token"]
    )


class ClientRoleCreateRequest(BaseModel):
    name: str
    attributes: dict = Field(default_factory=dict)
