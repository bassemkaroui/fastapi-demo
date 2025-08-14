import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, Response
from fastapi_pagination import add_pagination

from fastapi_demo.api.dependencies import rate_limit_dep
from fastapi_demo.api.exception_handlers import add_exception_handlers
from fastapi_demo.api.lifespan import lifespan
from fastapi_demo.api.main import api_router
from fastapi_demo.api.routes import health
from fastapi_demo.core.config import settings
from fastapi_demo.core.utils.identifiers import custom_generate_unique_id


def create_app(
    default_response_class: type[Response] = ORJSONResponse,
) -> FastAPI:
    kwargs = {"dependencies": None}
    if settings.RATE_LIMITING_ENABLED:
        kwargs["dependencies"] = [Depends(rate_limit_dep)]  # type: ignore[assignment]

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
        default_response_class=default_response_class,
        lifespan=lifespan,
        **kwargs,  # type: ignore[arg-type]
    )
    add_pagination(app)

    # add_middlewares(
    #     app,
    #     default_response_class=default_response_class,
    #     enable_rate_limit=settings.RATE_LIMITING_ENABLED,
    #     enable_rate_limit_headers=settings.RATE_LIMITING_HEADERS_ENABLED,
    # )

    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    add_exception_handlers(app, default_response_class)

    app.include_router(api_router, prefix=f"{settings.API_PREFIX}")
    app.include_router(health.router, prefix="/healthz", tags=["health"])

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
