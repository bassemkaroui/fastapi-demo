# import logging

from fastapi import FastAPI, Request, Response, status

from fastapi_demo.core.exceptions import (
    APIKeyNotFoundOrRevokedError,
    InvalidAPIKeyError,
    UserNotFoundError,
)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI, default_response_class: type[Response]) -> None:
    @app.exception_handler(APIKeyNotFoundOrRevokedError)
    async def api_key_not_found_or_revoked_exception_handler(
        request: Request, exc: APIKeyNotFoundOrRevokedError
    ) -> Response:
        # logger.exception(str(exc))
        return default_response_class(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)}
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_exception_handler(
        request: Request, exc: UserNotFoundError
    ) -> Response:
        # logger.exception(str(exc))
        return default_response_class(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": str(exc)}
        )

    @app.exception_handler(InvalidAPIKeyError)
    async def invalid_api_key_exception_handler(
        request: Request, exc: InvalidAPIKeyError
    ) -> Response:
        # logger.exception(str(exc))
        return default_response_class(
            status_code=status.HTTP_403_FORBIDDEN, content={"message": str(exc)}
        )
