from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_demo.core.db.engine import AsyncSessionMaker, SQLAlchemyAsyncSessionMaker
from fastapi_demo.core.models import metadata  # noqa: F401 # NOTE: this is used for migrations
from fastapi_demo.core.models.users import OAuthAccount, User


async def get_async_session() -> AsyncGenerator[SQLAlchemyAsyncSession]:
    async with SQLAlchemyAsyncSessionMaker() as session:
        yield session


async def get_async_sqlmodel_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionMaker() as session:
        yield session


async def get_user_db(session: Annotated[SQLAlchemyAsyncSession, Depends(get_async_session)]):  # type: ignore[no-untyped-def] # noqa: RUF029
    yield SQLModelUserDatabaseAsync(session, User, OAuthAccount)
