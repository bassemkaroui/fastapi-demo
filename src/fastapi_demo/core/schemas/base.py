from datetime import datetime
from typing import TypeVar

from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from pydantic import BaseModel, Field, field_validator
from sqlmodel import DateTime, SQLModel, func, text
from sqlmodel import Field as SQLModelField
from ulid import ULID

from fastapi_demo.core.db.types import PGULID

T = TypeVar("T")

CursorPage = CustomizedPage[BaseCursorPage[T], UseParamsFields(size=10)]


class Message(BaseModel):
    message: str


class PaginationParams(BaseModel):
    offset: int | None = Field(default=None, ge=0)
    limit: int | None = Field(default=None, ge=1)


class UserStateParams(BaseModel):
    is_active: bool | None = None
    is_verified: bool | None = None
    is_superuser: bool | None = None


class SearchParams(BaseModel):
    search: str | None = None


class QueryParams(PaginationParams, UserStateParams, SearchParams):
    pass


class PaginationAndSearchParams(PaginationParams, SearchParams):
    pass


class ULIDPrimaryKeyMixin(SQLModel):
    id: ULID = SQLModelField(  # type: ignore[call-overload]
        primary_key=True,
        nullable=False,
        sa_type=PGULID(),
        sa_column_kwargs={"server_default": text("gen_monotonic_ulid()")},
    )


class TimestampMixin(SQLModel):
    created_at: datetime = SQLModelField(  # type: ignore[call-overload]
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime = SQLModelField(  # type: ignore[call-overload]
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
        nullable=False,
    )


class UsernameMixin(BaseModel):
    @field_validator("first_name", "last_name", mode="before", check_fields=False)
    @classmethod
    def capitalize(cls, value: str) -> str:
        return value.strip().capitalize() if isinstance(value, str) else value
