import time
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated, cast

from fastapi import Depends, Header, HTTPException, Request, Response, status
from httpx import AsyncClient
from openfga_sdk import OpenFgaClient
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_demo.api.ratelimit import (
    get_client_ip,
    get_rate_limit_rules,
    limiter,
)
from fastapi_demo.core.auth.backends import redis_users_client
from fastapi_demo.core.auth.users import (
    current_superuser,
    current_verified_active_user,
    get_current_user,
)
from fastapi_demo.core.config import Settings
from fastapi_demo.core.db.engine import AsyncSessionMaker
from fastapi_demo.core.models.users import User
from fastapi_demo.core.services.api_key import APIKeyService
from fastapi_demo.core.services.token import TokenService
from fastapi_demo.core.services.user import UserService

# --- Settings Dependency ---


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, Depends(get_settings)]


# --- Session Dependency ---


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionMaker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# --- Async HTTP Client ---


async def get_http_client(request: Request) -> AsyncClient:
    return cast(AsyncClient, request.state.http_client)


HttpClientDep = Annotated[AsyncClient, Depends(get_http_client)]


# --- API Key ---


async def get_api_key_id(
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    if api_key is None:
        return None

    try:
        key_id, _ = api_key.split(".")
    except ValueError:
        raise HTTPException(  # noqa: B904
            status_code=status.HTTP_403_FORBIDDEN, detail="Malformed API Key"
        )
    return key_id


APIKeyIDDep = Annotated[str | None, Depends(get_api_key_id)]


# --- Users ---


CurrentVerifiedActiveUserDep = Annotated[User, Depends(current_verified_active_user)]
CurrentSuperUserDep = Annotated[User, Depends(current_superuser)]
# OptionalCurrentVerifiedActiveUserDep = Annotated[
#     User | None, Depends(optional_current_verified_active_user)
# ]
# OptionalCurrentSuperUserDep = Annotated[User | None, Depends(optional_current_superuser)]


# --- Rate Limit Dependency ---


async def rate_limit_dep(
    request: Request,
    response: Response,
    user: Annotated[User | None, Depends(get_current_user)],
    settings: SettingsDep,
) -> None:
    client_ip = get_client_ip(request)

    ip_key = f"ip:{client_ip}"
    # user_key = f"user:{user_id}" if user_id else None
    user_key = f"user:{user.id}" if user else None

    identifier = user_key or ip_key
    burst_rule, sustained_rule = get_rate_limit_rules(request, user_key)

    rate_limited_path = request.url.path != "/healthz/"
    headers = {}

    if rate_limited_path:
        allowed_burst = await limiter.hit(burst_rule, identifier)
        allowed_sustained = await limiter.hit(sustained_rule, identifier)

        if settings.RATE_LIMITING_HEADERS_ENABLED:
            reset_ts, remaining = await limiter.get_window_stats(sustained_rule, identifier)
            headers = {
                "X-RateLimit-Limit": str(sustained_rule.amount),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset_ts - time.time())),
            }
            response.headers.update(headers)

        if not (allowed_burst and allowed_sustained):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": f"Rate limit exceeded: {burst_rule} and {sustained_rule}."},
                headers=headers,
            )


# --- User Service Dependency ---


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


# --- Token Service Dependency ---


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(redis_users_client, settings.REDIS_USERS_TOKEN_KEY_PREFIX)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


# --- APIKey Service Dependency ---


def get_api_key_service(session: SessionDep, settings: SettingsDep) -> APIKeyService:
    return APIKeyService(session, settings)


APIKeyServiceDep = Annotated[APIKeyService, Depends(get_api_key_service)]


# --- OpenFGA dependencies ---


async def get_openfga_client(request: Request) -> OpenFgaClient:
    return request.state.fga_client


OpenFGAClientDep = Annotated[OpenFgaClient, Depends(get_openfga_client)]
