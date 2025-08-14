from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi.security import APIKeyHeader
from fastapi_users import exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    # JWTStrategy,
    RedisStrategy,
    Strategy,
    Transport,
)
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from fastapi_demo.core.auth.manager import UserManager
from fastapi_demo.core.config import settings
from fastapi_demo.core.db.engine import AsyncSessionMaker
from fastapi_demo.core.exceptions import InvalidAPIKeyError
from fastapi_demo.core.models.users import APIKey, User

# --- Redis Backend ---

relative_api_prefix = settings.API_PREFIX.lstrip("/")
redis_bearer_transport = BearerTransport(tokenUrl=f"{relative_api_prefix}/auth/login")
redis_users_client = aioredis.from_url(
    str(settings.REDIS_URI), decode_responses=True, db=settings.REDIS_USERS_DB
)


def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(
        redis_users_client,
        lifetime_seconds=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        key_prefix=settings.REDIS_USERS_TOKEN_KEY_PREFIX,
    )


redis_auth_backend = AuthenticationBackend(
    name="redis",
    transport=redis_bearer_transport,
    get_strategy=get_redis_strategy,
)


# --- JWT Backend ---

# jwt_bearer_transport = BearerTransport(tokenUrl=f"{relative_api_prefix}/jwt/login")
#
#
# def get_jwt_strategy() -> jwtstrategy:
#     return jwtstrategy(
#         secret=settings.SECRET_KEY, lifetime_seconds=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )
#
#
# jwt_auth_backend = AuthenticationBackend(
#     name="jwt",
#     transport=jwt_bearer_transport,
#     get_strategy=get_jwt_strategy,
# )

# --- API Keys Backend ---


class APIKeyTransport(Transport):
    scheme: APIKeyHeader

    def __init__(self, name: str):
        self.scheme = APIKeyHeader(name=name, auto_error=False)


class APIKeyStrategy(Strategy[User, ULID]):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        redis: aioredis.Redis,
        lifetime_seconds: int,
        key_prefix: str,
    ):
        self.session_factory = session_factory
        self.hasher = Argon2Hasher()
        self.redis = redis
        self.lifetime_seconds = lifetime_seconds
        self.key_prefix = key_prefix

    async def read_token(self, token: str | None, user_manager: UserManager) -> User | None:  # type: ignore[override]  # noqa: C901
        api_key = token
        if api_key is None:
            return None

        try:
            key_id, key_secret = api_key.split(".", maxsplit=1)
        except ValueError:
            raise InvalidAPIKeyError(key_id) from None

        cache_key = f"{self.key_prefix}{key_id}"
        ttl = await self.redis.ttl(cache_key)
        if ttl > 0:
            if ttl < 60:  # noqa: PLR2004
                await self.redis.expire(cache_key, self.lifetime_seconds)
            cached = await self.redis.hgetall(cache_key)  # type: ignore[misc]
            if cached:
                try:
                    user_id = user_manager.parse_id(cached["owner_id"])
                except (exceptions.UserNotExists, exceptions.InvalidID, KeyError):
                    return None
                else:
                    return await user_manager.get(user_id)

        async with self.session_factory() as session:
            statement = (
                select(APIKey).where(APIKey.revoked == False).where(APIKey.key_id == key_id)  # noqa: E712
            )
            result = await session.exec(statement)
            db_key = result.first()
            if not db_key or not self.hasher.verify(key_secret, db_key.key_hash):
                raise InvalidAPIKeyError(key_id)

            db_key.last_used = datetime.now(timezone.utc)
            session.add(db_key)
            await session.commit()

            metadata = {"owner_id": str(db_key.owner_id)}
            await self.redis.hset(cache_key, mapping=metadata)  # type: ignore[misc]
            await self.redis.expire(cache_key, self.lifetime_seconds)

            try:
                user_id = user_manager.parse_id(db_key.owner_id)
            except (exceptions.UserNotExists, exceptions.InvalidID, KeyError):
                return None
            else:
                return await user_manager.get(db_key.owner_id)


api_key_transport = APIKeyTransport(name="X-API-Key")  # type: ignore[abstract]


def get_api_key_strategy() -> APIKeyStrategy:
    return APIKeyStrategy(  # type: ignore[abstract]
        AsyncSessionMaker,
        redis_users_client,
        lifetime_seconds=60 * settings.API_KEY_EXPIRE_MINUTES,
        key_prefix=settings.REDIS_USERS_APIKEY_KEY_PREFIX,
    )


api_key_backend = AuthenticationBackend(
    name="api_key",
    transport=api_key_transport,
    get_strategy=get_api_key_strategy,
)
