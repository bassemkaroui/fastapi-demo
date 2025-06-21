from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from pydantic import UUID4

from fastapi_demo.api.dependencies import TokenServiceDep
from fastapi_demo.core.auth.backends import redis_auth_backend
from fastapi_demo.core.auth.oauth import google_oauth_client
from fastapi_demo.core.auth.users import current_superuser, fastapi_users
from fastapi_demo.core.config import settings
from fastapi_demo.core.schemas.users import UserCreate, UserRead

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(redis_auth_backend, requires_verification=True),
    prefix="/auth",
    tags=["auth"],
)
# router.include_router(
#     fastapi_users.get_auth_router(jwt_auth_backend, requires_verification=True),
#     prefix="/auth/jwt",
#     tags=["auth"],
# )
router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        redis_auth_backend,
        settings.SECRET_KEY,
        # redirect_url="http://localhost:8501/oauth-callback",
        redirect_url=str(settings.FRONTEND_HOST),
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/auth/google",
    tags=["oauth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/auth/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    tags=["auth"],
)
async def revoke_token(token: Annotated[str, Body(embed=True)], service: TokenServiceDep):
    await service.revoke(token)


@router.post(
    "/auth/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    tags=["auth"],
)
async def revoke_all_tokens(user_id: Annotated[UUID4, Body(embed=True)], service: TokenServiceDep):
    await service.revoke_all_for_user(user_id)
