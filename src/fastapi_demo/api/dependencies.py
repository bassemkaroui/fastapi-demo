from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_demo.core.auth.backends import redis_users_client
from fastapi_demo.core.config import Settings
from fastapi_demo.core.db import async_sqlmodel_session_maker
from fastapi_demo.core.services.token import TokenService


async def get_async_sqlmodel_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_sqlmodel_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_async_sqlmodel_session)]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(redis_users_client, settings.REDIS_USERS_KEY_PREFIX)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
