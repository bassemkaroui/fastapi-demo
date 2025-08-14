from datetime import datetime
from typing import Optional

from fastapi_users_db_sqlmodel import SQLModelBaseOAuthAccount, SQLModelBaseUserDB
from sqlmodel import DateTime, Field, ForeignKey, Index, Relationship, SQLModel
from ulid import ULID

from fastapi_demo.core.db.types import PGULID
from fastapi_demo.core.schemas.base import TimestampMixin, ULIDPrimaryKeyMixin


class OAuthAccount(ULIDPrimaryKeyMixin, SQLModelBaseOAuthAccount, table=True):  # type: ignore[misc]
    user_id: ULID = Field(  # type: ignore[assignment]
        sa_column_args=(ForeignKey("user.id", ondelete="CASCADE"),),
        nullable=False,
        sa_type=PGULID(),
    )

    user: Optional["User"] = Relationship(
        back_populates="oauth_accounts", sa_relationship_kwargs={"lazy": "joined"}
    )


class APIKey(ULIDPrimaryKeyMixin, TimestampMixin, SQLModel, table=True):
    __tablename__ = "apikey"
    __table_args__ = (
        Index("ix_key_id_revoked", "key_id", "revoked"),
        Index(
            "ix_apikey_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )
    key_id: str = Field(nullable=False, unique=True, index=True)
    key_hash: str = Field(nullable=False)
    key_preview: str = Field(nullable=False)
    name: str = Field(max_length=255, nullable=False)
    owner_id: ULID = Field(foreign_key="user.id", nullable=False, index=True, sa_type=PGULID())  # type: ignore[call-overload]
    last_used: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=True)  # type: ignore[call-overload]
    revoked: bool = Field(default=False)

    user: Optional["User"] = Relationship(
        back_populates="api_keys", sa_relationship_kwargs={"lazy": "selectin"}
    )


class User(ULIDPrimaryKeyMixin, TimestampMixin, SQLModelBaseUserDB, table=True):  # type: ignore[misc]
    __table_args__ = (
        Index(
            "ix_user_first_name_trgm",
            "first_name",
            postgresql_using="gin",
            postgresql_ops={"first_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_user_last_name_trgm",
            "last_name",
            postgresql_using="gin",
            postgresql_ops={"last_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_user_email_trgm",
            "email",
            postgresql_using="gin",
            postgresql_ops={"email": "gin_trgm_ops"},
        ),
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
    api_keys: list[APIKey] = Relationship(
        back_populates="user",
        passive_deletes=True,
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
    )
