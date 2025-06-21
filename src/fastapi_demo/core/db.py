from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from fastapi_demo.core.config import settings
from fastapi_demo.core.models import metadata  # noqa: F401 # NOTE: this is used for migrations
from fastapi_demo.core.models.users import OAuthAccount, User

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# engine = create_async_engine(DATABASE_URL, future=True)
engine = create_async_engine(str(settings.POSTGRES_URI), future=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
async_sqlmodel_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=SQLModelAsyncSession
)


# NOTE: This won't be used in the case of using **alembic**
async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: Annotated[AsyncSession, Depends(get_async_session)]):  # type: ignore[no-untyped-def] # noqa: RUF029
    yield SQLModelUserDatabaseAsync(session, User, OAuthAccount)
