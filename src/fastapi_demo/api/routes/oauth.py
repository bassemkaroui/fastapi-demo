from fastapi import APIRouter

from fastapi_demo.core.auth.backends import redis_auth_backend
from fastapi_demo.core.auth.oauth import github_oauth_client, google_oauth_client
from fastapi_demo.core.auth.users import (
    fastapi_users,
)
from fastapi_demo.core.config import settings

router = APIRouter()

router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        redis_auth_backend,
        settings.SECRET_KEY,
        redirect_url=str(settings.GOOGLE_REDIRECT_URL),
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/google",
)

router.include_router(
    fastapi_users.get_oauth_router(
        github_oauth_client,
        redis_auth_backend,
        settings.SECRET_KEY,
        redirect_url=str(settings.GITHUB_REDIRECT_URL),
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/github",
)
