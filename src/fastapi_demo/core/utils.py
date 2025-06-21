import contextlib
from typing import TYPE_CHECKING, cast

from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from fastapi_mail import FastMail
from fastapi_users.exceptions import UserAlreadyExists

from fastapi_demo.core.auth.manager import get_user_manager
from fastapi_demo.core.config import settings
from fastapi_demo.core.db import get_async_session, get_user_db
from fastapi_demo.core.schemas.users import UserCreate

if TYPE_CHECKING:
    from fastapi_demo.core.models.users import User


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(
    email: str, password: str, is_superuser: bool = False, is_verified: bool = False
) -> "User":
    try:
        async with get_async_session_context() as session:  # noqa: SIM117
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(
                    user_db, BackgroundTasks(), FastMail(settings.mailer_config)
                ) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_superuser=is_superuser,
                            is_verified=is_verified,
                        )
                    )
                    print(f"User created {user}")
                    return cast("User", user)
    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise


# --- Initialize DB with a superuser ---
async def init_db() -> None:
    with contextlib.suppress(UserAlreadyExists):
        await create_user(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            is_verified=True,
        )
