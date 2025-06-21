from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from sqlmodel import DateTime, SQLModel, func
from sqlmodel import Field as SQLModelField


class Message(BaseModel):
    message: str


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, gt=1)


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
