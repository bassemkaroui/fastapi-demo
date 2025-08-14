import re
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, InvalidPasswordException, exceptions
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from ulid import ULID

from fastapi_demo.core.celery.tasks.emails import (
    send_reset_password_email,
    send_verify_account_email,
    send_welcome_email,
)
from fastapi_demo.core.config import settings
from fastapi_demo.core.db.dependencies import get_user_db
from fastapi_demo.core.models.users import User
from fastapi_demo.core.schemas.users import UserCreate

SECRET = settings.SECRET_KEY


class ULIDIDMixin:
    def parse_id(self, value: Any) -> ULID:  # noqa: PLR6301
        if isinstance(value, ULID):
            return value
        if isinstance(value, str):
            try:
                return ULID.from_str(value)  # type: ignore[no-any-return]
            except ValueError as e:
                raise exceptions.InvalidID() from e
        if isinstance(value, bytes):
            try:
                return ULID.from_bytes(value)  # type: ignore[no-any-return]
            except ValueError as e:
                raise exceptions.InvalidID() from e
        if isinstance(value, uuid.UUID):
            try:
                return ULID.from_uuid(value)  # type: ignore[no-any-return]
            except ValueError as e:
                raise exceptions.InvalidID() from e
        raise exceptions.InvalidID()


class UserManager(ULIDIDMixin, BaseUserManager[User, ULID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    def __init__(
        self,
        user_db: SQLModelUserDatabaseAsync,
        **kwargs: Any,
    ):
        super().__init__(user_db, **kwargs)

    async def validate_password(  # noqa: PLR6301
        self,
        password: str,
        user: UserCreate | User,  # type:ignore[override]
    ) -> None:
        if len(password) < settings.USER_PASSWORD_MIN_LENGTH:
            raise InvalidPasswordException(reason="Password should be at least 8 characters")
        if len(password) > settings.USER_PASSWORD_MAX_LENGTH:
            raise InvalidPasswordException(reason="Password should be at most 40 characters")
        if user.email in password:
            raise InvalidPasswordException(reason="Password should not contain e-mail")
        if not re.search(r"[A-Z]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one uppercase letter"
            )
        if not re.search(r"[a-z]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one lowercase letter"
            )
        if not re.search(r"\d", password):
            raise InvalidPasswordException(reason="Password must contain at least one digit")
        if not re.search(r"[^\w\s]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one special character"
            )

    async def on_after_register(self, user: User, request: Request | None = None) -> None:  # noqa: ARG002, PLR6301
        # print(f"User {user.id} has registered.")
        user_data = {"email": user.email, "first_name": user.first_name}
        send_welcome_email.delay(user_data)

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        # print(f"User {user.id} has forgot their password. Reset token: {token}")
        user_data = {"email": user.email, "first_name": user.first_name}
        link = f"{str(settings.FRONTEND_HOST).rstrip('/')}/?action=reset&token={token}"
        ttl_minutes = self.reset_password_token_lifetime_seconds // 60
        send_reset_password_email.delay(user_data, link, ttl_minutes)

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        # print(f"Verification requested for user {user.id}. Verification token: {token}")
        user_data = {"email": user.email, "first_name": user.first_name}
        link = f"{str(settings.FRONTEND_HOST).rstrip('/')}/?action=verify&token={token}"
        ttl_minutes = self.verification_token_lifetime_seconds // 60
        send_verify_account_email.delay(user_data, link, ttl_minutes)


async def get_user_manager(  # noqa: RUF029
    user_db: Annotated[SQLModelUserDatabaseAsync, Depends(get_user_db)],
) -> AsyncGenerator[UserManager]:
    # yield UserManager(user_db=user_db, password_helper=password_helper)
    yield UserManager(user_db=user_db)
