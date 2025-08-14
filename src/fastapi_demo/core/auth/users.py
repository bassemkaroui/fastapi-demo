from typing import Annotated

# from fastapi import Request
from fastapi import Depends, HTTPException, Request, status
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from ulid import ULID

from fastapi_demo.core.auth.backends import api_key_backend, redis_auth_backend
from fastapi_demo.core.auth.manager import get_user_manager
from fastapi_demo.core.config import settings
from fastapi_demo.core.models.users import User


async def get_enabled_backends(request: Request) -> list[AuthenticationBackend]:  # noqa: RUF029
    """Return the enabled backends based on the routes"""
    request_path = request.url.path.split(settings.API_PREFIX.rstrip("/"))[-1]
    if request_path.startswith(("/auth/", "/users/")):
        return [redis_auth_backend]
    return [api_key_backend, redis_auth_backend]


fastapi_users = FastAPIUsers[User, ULID](
    get_user_manager,
    [redis_auth_backend, api_key_backend],
)

if settings.USE_DYNAMICALLY_ENABLED_AUTH_BACKENDS:
    get_current_user = fastapi_users.current_user(
        optional=True, get_enabled_backends=get_enabled_backends
    )
else:
    get_current_user = fastapi_users.current_user(optional=True)


async def current_verified_active_user(  # noqa: RUF029
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    status_code = status.HTTP_401_UNAUTHORIZED
    if user:
        status_code = status.HTTP_403_FORBIDDEN
        if not user.is_active:
            status_code = status.HTTP_401_UNAUTHORIZED
            user = None
        elif not user.is_verified:
            user = None
    if not user:
        raise HTTPException(status_code=status_code)
    return user


async def current_superuser(  # noqa: RUF029
    user: Annotated[User, Depends(current_verified_active_user)],
) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


# current_verified_active_user = fastapi_users.current_user(active=True, verified=True)
# current_superuser = fastapi_users.current_user(active=True, verified=True, superuser=True)
#
# optional_current_verified_active_user = fastapi_users.current_user(
#     optional=True, active=True, verified=True
# )
# optional_current_superuser = fastapi_users.current_user(
#     optional=True, active=True, verified=True, superuser=True
# )

# # --- With Dynamically Enabled Backends ---
# current_verified_active_user = fastapi_users.current_user(
#     active=True, verified=True, get_enabled_backends=get_enabled_backends
# )
# current_superuser = fastapi_users.current_user(
#     active=True, verified=True, superuser=True, get_enabled_backends=get_enabled_backends
# )
#
# optional_current_verified_active_user = fastapi_users.current_user(
#     optional=True, active=True, verified=True, get_enabled_backends=get_enabled_backends
# )
# optional_current_superuser = fastapi_users.current_user(
#     optional=True,
#     active=True,
#     verified=True,
#     superuser=True,
#     get_enabled_backends=get_enabled_backends,
# )
