from datetime import datetime

from pydantic import BaseModel, Field
from ulid import ULID


class APIKeyBase(BaseModel):
    key_id: str
    key_preview: str
    name: str = Field(max_length=255)
    created_at: datetime


class APIKeyCreateResponse(APIKeyBase):
    api_key: str


class APIKeyCreateRequest(BaseModel):
    name: str = Field(max_length=40)


class APIKeyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=40)


class APIKeyRead(APIKeyBase):
    last_used: datetime | None = None


class RevokedAPIKeys(BaseModel):
    user_id: ULID
    number_of_revoked_api_keys: int
