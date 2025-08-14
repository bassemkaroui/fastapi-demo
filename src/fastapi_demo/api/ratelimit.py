from fastapi import Request
from limits import RateLimitItemPerMinute, RateLimitItemPerSecond
from limits.aio.storage import RedisStorage
from limits.aio.strategies import STRATEGIES

from fastapi_demo.core.config import settings

auth_burst_limit = RateLimitItemPerSecond(settings.RATE_LIMIT_VALUE_PER_SECOND_AUTH)
loggedin_burst_limit = RateLimitItemPerSecond(settings.RATE_LIMIT_VALUE_PER_SECOND_LOGGEDIN)
public_burst_limit = RateLimitItemPerSecond(settings.RATE_LIMIT_VALUE_PER_SECOND_PUBLIC)

auth_sustained_limit = RateLimitItemPerMinute(settings.RATE_LIMIT_VALUE_PER_MINUTE_AUTH)
loggedin_sustained_limit = RateLimitItemPerMinute(settings.RATE_LIMIT_VALUE_PER_MINUTE_LOGGEDIN)
public_sustained_limit = RateLimitItemPerMinute(settings.RATE_LIMIT_VALUE_PER_MINUTE_PUBLIC)

storage = RedisStorage(settings.rate_limiter_storage_uri, implementation="redispy")
strategy = STRATEGIES[settings.RATE_LIMITING_STRATEGY]
limiter = strategy(storage)  # type: ignore[abstract]


def get_client_ip(request: Request) -> str:
    # if behind a load-balancer or an API gateway
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        "127.0.0.1"
    return ip


# @cached(
#     **settings.RATE_LIMITING_USERS_CACHE_REDIS_CONFIG,
#     key_builder=lambda func,
#     token,
#     api_key: f"token={token};api_key={api_key.split('.', maxsplit=1)[0] if api_key else api_key}",
# )
# async def get_user_id(token: str | None = None, api_key: str | None = None) -> UUID4 | str | None:
#     if token:
#         return await redis_users_client.get(f"{settings.REDIS_USERS_TOKEN_KEY_PREFIX}{token}")  # type: ignore[no-any-return]
#     if api_key:
#         return await redis_users_client.get(
#             f"{settings.REDIS_USERS_APIKEY_KEY_PREFIX}{api_key.split('.', maxsplit=1)[0]}"
#         )  # type: ignore[no-any-return]
#     return None


def get_rate_limit_rules(
    request: Request, user_key: str | None
) -> tuple[RateLimitItemPerSecond, RateLimitItemPerMinute]:
    if "/auth/" in request.url.path:
        burst_rule = auth_burst_limit
        sustained_rule = auth_sustained_limit
    elif user_key:
        burst_rule = loggedin_burst_limit
        sustained_rule = loggedin_sustained_limit
    else:
        burst_rule = public_burst_limit
        sustained_rule = public_sustained_limit
    return (burst_rule, sustained_rule)
