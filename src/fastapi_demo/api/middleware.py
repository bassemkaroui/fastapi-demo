import time

from fastapi import FastAPI, Request, Response, status

from fastapi_demo.api.ratelimit import (
    get_client_ip,
    get_rate_limit_rules,
    get_user_id,
    limiter,
)


def add_middlewares(
    app: FastAPI,
    default_response_class: type[Response],
    enable_rate_limit: bool = True,
    enable_rate_limit_headers: bool = False,
) -> None:
    if not enable_rate_limit:
        return

    @app.middleware("html")
    async def rate_limit_middleware(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        client_ip = get_client_ip(request)

        auth_header = request.headers.get("authorization", "")

        user_id = None
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split()[1]
            user_id = await get_user_id(token)

        ip_key = f"ip:{client_ip}"
        user_key = f"user:{user_id}" if user_id else None

        burst_rule, sustained_rule = get_rate_limit_rules(request, user_key)
        identifier = user_key or ip_key

        allowed_burst = await limiter.hit(burst_rule, identifier)
        allowed_sustained = await limiter.hit(sustained_rule, identifier)

        if enable_rate_limit_headers:
            reset_ts, remaining = await limiter.get_window_stats(sustained_rule, identifier)
            headers = {
                "X-RateLimit-Limit": str(sustained_rule.amount),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset_ts - time.time())),
            }
        else:
            headers = {}

        if not (allowed_burst and allowed_sustained):
            return default_response_class(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": f"Rate limit exceeded: {burst_rule} and {sustained_rule}."},
                headers=headers,
            )

        response = await call_next(request)
        response.headers.update(headers)
        return response  # type: ignore[no-any-return]
