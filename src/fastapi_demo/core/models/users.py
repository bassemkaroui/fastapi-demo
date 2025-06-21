from typing import Optional

from fastapi_users_db_sqlmodel import SQLModelBaseOAuthAccount, SQLModelBaseUserDB
from pydantic import UUID4
from sqlmodel import Field, ForeignKey, Relationship, text

from fastapi_demo.core.schemas.base import TimestampMixin


class OAuthAccount(SQLModelBaseOAuthAccount, table=True):
    user_id: UUID4 = Field(
        sa_column_args=(ForeignKey("user.id", ondelete="CASCADE"),), nullable=False
    )
    user: Optional["User"] = Relationship(back_populates="oauth_accounts")


class User(SQLModelBaseUserDB, TimestampMixin, table=True):
    id: UUID4 = Field(
        primary_key=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    oauth_accounts: list[OAuthAccount] = Relationship(
        back_populates="user",
        passive_deletes=True,
        sa_relationship_kwargs={
            "lazy": "joined",
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
    )
