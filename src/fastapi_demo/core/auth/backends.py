import redis.asyncio as aioredis
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    # JWTStrategy,
    RedisStrategy,
)

from fastapi_demo.core.config import settings

redis_bearer_transport = BearerTransport(tokenUrl="api/auth/login")
redis_users_client = aioredis.from_url(
    str(settings.REDIS_URI), decode_responses=True, db=settings.REDIS_USERS_DB
)


def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(
        redis_users_client,
        lifetime_seconds=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        key_prefix=settings.REDIS_USERS_KEY_PREFIX,
    )


redis_auth_backend = AuthenticationBackend(
    name="redis",
    transport=redis_bearer_transport,
    get_strategy=get_redis_strategy,
)


# jwt_bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
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
