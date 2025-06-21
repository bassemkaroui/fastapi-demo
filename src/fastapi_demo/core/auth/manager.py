import re
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, Request
from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi_users import BaseUserManager, InvalidPasswordException, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync

from fastapi_demo.api.dependencies import SettingsDep
from fastapi_demo.core.config import settings
from fastapi_demo.core.db import get_user_db
from fastapi_demo.core.models.users import User
from fastapi_demo.core.schemas.users import UserCreate

SECRET = settings.SECRET_KEY


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    def __init__(
        self,
        user_db: SQLModelUserDatabaseAsync,
        background_tasks: BackgroundTasks,
        mailer: FastMail,
        **kwargs: Any,
    ):
        super().__init__(user_db, **kwargs)
        self.background_tasks = background_tasks
        self.mailer = mailer

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

    async def on_after_register(self, user: User, request: Request | None = None) -> None:  # noqa: ARG002
        # print(f"User {user.id} has registered.")
        message = MessageSchema(
            subject="Welcome to fastapi-demo! 🎉",
            recipients=[user.email],
            template_body={"project_name": settings.PROJECT_NAME, "user": user},
            subtype=MessageType.html,
        )
        self.background_tasks.add_task(
            self.mailer.send_message, message, template_name="new_account.html"
        )

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        # print(f"User {user.id} has forgot their password. Reset token: {token}")
        link = f"{str(settings.FRONTEND_HOST).rstrip('/')}/?action=reset&token={token}"
        message = MessageSchema(
            subject="Reset your fastapi-demo password",
            recipients=[user.email],
            template_body={
                "project_name": settings.PROJECT_NAME,
                "user": user,
                "link": link,
                "reset_password_token_lifetime_minutes": self.reset_password_token_lifetime_seconds
                // 60,
            },
            subtype=MessageType.html,
        )
        self.background_tasks.add_task(
            self.mailer.send_message, message, template_name="reset_password.html"
        )

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        # print(f"Verification requested for user {user.id}. Verification token: {token}")
        link = f"{str(settings.FRONTEND_HOST).rstrip('/')}/?action=verify&token={token}"
        message = MessageSchema(
            subject="Confirm your fastapi-demo account 🛡️",
            recipients=[user.email],
            template_body={
                "project_name": settings.PROJECT_NAME,
                "user": user,
                "link": link,
                "verification_token_lifetime_minutes": self.verification_token_lifetime_seconds
                // 60,
            },
            subtype=MessageType.html,
        )
        self.background_tasks.add_task(
            self.mailer.send_message, message, template_name="verify_account.html"
        )


async def get_mailer(settings: SettingsDep) -> FastMail:  # noqa: RUF029
    return FastMail(settings.mailer_config)


async def get_user_manager(  # noqa: RUF029
    user_db: Annotated[SQLModelUserDatabaseAsync, Depends(get_user_db)],
    background_tasks: BackgroundTasks,
    mailer: Annotated[FastMail, Depends(get_mailer)],
) -> AsyncGenerator[UserManager]:
    # yield UserManager(
    #     user_db=user_db,
    #     background_tasks=background_tasks,
    #     mailer=mailer,
    #     password_helper=password_helper,
    # )
    yield UserManager(user_db=user_db, background_tasks=background_tasks, mailer=mailer)
