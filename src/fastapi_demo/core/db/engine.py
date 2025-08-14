from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_demo.core.config import settings
from fastapi_demo.core.models import metadata  # noqa: F401 # NOTE: this is used for migrations

engine = create_async_engine(
    str(settings.POSTGRES_URI),
    future=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_recycle=settings.POOL_RECYCLE,
    pool_pre_ping=settings.POOL_PRE_PING,
    pool_timeout=settings.POOL_TIMEOUT,
)
SQLAlchemyAsyncSessionMaker = async_sessionmaker(
    engine, expire_on_commit=False, class_=SQLAlchemyAsyncSession
)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# # NOTE: This won't be used in the case of using **alembic**
# async def create_db_and_tables() -> None:
#     async with engine.begin() as conn:
#         # await conn.run_sync(metadata.drop_all)
#         await conn.run_sync(metadata.create_all)
