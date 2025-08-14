from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import Field
from ulid import ULID

from fastapi_demo.core.schemas.base import TimestampMixin, UsernameMixin


class UserRead(BaseUser[ULID], TimestampMixin, UsernameMixin):  # type: ignore[misc]
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)


class UserCreate(BaseUserCreate, UsernameMixin):
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)


class UserUpdate(BaseUserUpdate, UsernameMixin):
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
