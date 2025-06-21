from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, Response

from fastapi_demo.api.main import api_router
from fastapi_demo.api.middleware import add_middlewares
from fastapi_demo.core.config import settings

# from fastapi_demo.core.db import create_db_and_tables
from fastapi_demo.core.utils import custom_generate_unique_id  # , init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001, RUF029
    # await create_db_and_tables()  # NOTE: This should be replaced with **alembic**
    # await init_db()
    yield


def create_app(
    default_response_class: type[Response] = ORJSONResponse,
) -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
        default_response_class=default_response_class,
        lifespan=lifespan,
    )

    add_middlewares(
        app,
        default_response_class=default_response_class,
        enable_rate_limit=settings.RATE_LIMITING_ENABLED,
        enable_rate_limit_headers=settings.RATE_LIMITING_HEADERS_ENABLED,
    )

    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=f"{settings.API_PREFIX}")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
