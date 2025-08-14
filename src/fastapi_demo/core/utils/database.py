import contextlib
from typing import TYPE_CHECKING, cast

from fastapi_users.exceptions import UserAlreadyExists

from fastapi_demo.core.auth.manager import get_user_manager
from fastapi_demo.core.config import settings
from fastapi_demo.core.db.dependencies import get_async_session, get_user_db
from fastapi_demo.core.db.engine import AsyncSessionMaker
from fastapi_demo.core.schemas.api_keys import APIKeyCreateRequest
from fastapi_demo.core.schemas.users import UserCreate
from fastapi_demo.core.services.api_key import APIKeyService

if TYPE_CHECKING:
    from fastapi_demo.core.models.users import User


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(
    email: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
    is_superuser: bool = False,
    is_verified: bool = False,
) -> "User":
    try:
        # Create user
        async with get_async_session_context() as session:  # noqa: SIM117
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_superuser=is_superuser,
                            is_verified=is_verified,
                            first_name=first_name,
                            last_name=last_name,
                        )
                    )
                    print(f"User created {user}")
                    user_id = user.id
        async with AsyncSessionMaker() as session:
            api_key_data = await APIKeyService(session, settings).create_api_key(
                owner_id=user_id, api_key_create=APIKeyCreateRequest(name="default_api_key")
            )
            print(api_key_data)
    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise
    else:
        return cast("User", user)


# --- Initialize DB with a superuser ---
async def init_db() -> None:
    with contextlib.suppress(UserAlreadyExists):
        await create_user(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            is_verified=True,
        )
