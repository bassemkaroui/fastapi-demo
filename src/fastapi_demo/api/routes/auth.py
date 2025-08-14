from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from ulid import ULID

from fastapi_demo.api.dependencies import (
    APIKeyServiceDep,
    TokenServiceDep,
)
from fastapi_demo.core.auth.backends import redis_auth_backend
from fastapi_demo.core.auth.users import (
    current_superuser,
    fastapi_users,
)
from fastapi_demo.core.schemas.users import UserCreate, UserRead

router = APIRouter()

router.include_router(fastapi_users.get_auth_router(redis_auth_backend, requires_verification=True))
# router.include_router(
#     fastapi_users.get_auth_router(jwt_auth_backend, requires_verification=True), prefix="/jwt"
# )
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))


# --- Token Revocation ---


@router.post(
    "/tokens/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def revoke_token(token: Annotated[str, Body(embed=True)], service: TokenServiceDep):
    await service.revoke(token)


@router.post(
    "/tokens/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def revoke_all_tokens(user_id: Annotated[ULID, Body(embed=True)], service: TokenServiceDep):
    await service.revoke_all_for_user(user_id)


# --- API Key Revocation ---


@router.post(
    "/api-keys/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def revoke_api_key(api_key_id: Annotated[str, Body(embed=True)], service: APIKeyServiceDep):
    await service.revoke_api_key(api_key_id)


@router.post(
    "/api-keys/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def revoke_user_all_api_keys(
    user_id: Annotated[ULID, Body(embed=True)], service: APIKeyServiceDep
):
    revoked_count = await service.revoke_user_all_api_keys(user_id)
    return {"user_id": user_id, "number_of_revoked_api_keys": revoked_count}
