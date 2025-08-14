from typing import Annotated

from fastapi import Depends, Query, status
from ulid import ULID

from fastapi_demo.api.dependencies import (
    APIKeyServiceDep,
    CurrentVerifiedActiveUserDep,
    UserServiceDep,
)
from fastapi_demo.core.auth.users import current_superuser, fastapi_users
from fastapi_demo.core.schemas.api_keys import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyRead,
    APIKeyUpdate,
    RevokedAPIKeys,
)
from fastapi_demo.core.schemas.base import CursorPage
from fastapi_demo.core.schemas.users import UserRead, UserUpdate

router = fastapi_users.get_users_router(UserRead, UserUpdate)

# --- All Users ---


@router.get("/", response_model=CursorPage[UserRead], dependencies=[Depends(current_superuser)])
async def read_all_users(
    service: UserServiceDep,
    is_active: Annotated[bool | None, Query()] = None,
    is_verified: Annotated[bool | None, Query] = None,
    is_superuser: Annotated[bool | None, Query] = None,
    search: Annotated[str | None, Query()] = None,
):
    return await service.read_all_users(
        is_active=is_active, is_verified=is_verified, is_superuser=is_superuser, search=search
    )


# async def read_all_users(service: UserServiceDep, query_params: Annotated[QueryParams, Query()]):
#     return await service.read_all_users(**query_params.model_dump())


# --- Users API Keys Management ---


@router.get("/me/keys/", response_model=CursorPage[APIKeyRead], tags=["api_keys"])
async def read_all_my_api_keys(
    user: CurrentVerifiedActiveUserDep,
    service: APIKeyServiceDep,
    search: Annotated[str | None, Query()] = None,
):
    return await service.read_user_all_api_keys(
        owner_id=user.id,
        search=search,
        verify_user=False,
    )


@router.post("/me/keys/", response_model=APIKeyCreateResponse, tags=["api_keys"])
async def create_personal_key(
    user: CurrentVerifiedActiveUserDep,
    api_key_create: APIKeyCreateRequest,
    service: APIKeyServiceDep,
):
    key_data = await service.create_api_key(api_key_create, user.id, verify_user=False)
    return key_data


@router.patch("/me/keys/{key_id}", response_model=APIKeyRead, tags=["api_keys"])
async def update_api_key(
    key_id: str,
    api_key_update: APIKeyUpdate,
    current_user: CurrentVerifiedActiveUserDep,
    service: APIKeyServiceDep,
):
    return await service.update_api_key(key_id, api_key_update, current_user.id, verify_user=False)


# --- User API Keys Revocation ---


@router.post("/me/keys/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT, tags=["api_keys"])
async def revoke_my_api_key(
    key_id: str, service: APIKeyServiceDep, user: CurrentVerifiedActiveUserDep
):
    await service.revoke_api_key(key_id, user.id, verify_user=False)


@router.post("/me/keys/revoke-all", response_model=RevokedAPIKeys, tags=["api_keys"])
async def revoke_all_my_api_keys(service: APIKeyServiceDep, user: CurrentVerifiedActiveUserDep):
    revoked_count = await service.revoke_user_all_api_keys(user.id, verify_user=False)
    return {"user_id": user.id, "number_of_revoked_api_keys": revoked_count}


# --- **Admin Secion** ---


# --- Users API Keys Management ---


@router.get(
    "/{user_id}/keys/",
    response_model=CursorPage[APIKeyRead],
    dependencies=[Depends(current_superuser)],
    tags=["api_keys"],
)
async def read_user_all_api_keys(
    user_id: ULID, service: APIKeyServiceDep, search: Annotated[str | None, Query()] = None
):
    return await service.read_user_all_api_keys(owner_id=user_id, search=search)


@router.post(
    "/{user_id}/keys/",
    response_model=APIKeyCreateResponse,
    dependencies=[Depends(current_superuser)],
    tags=["api_keys"],
)
async def create_key_for_user(
    user_id: ULID, api_key_create: APIKeyCreateRequest, service: APIKeyServiceDep
):
    key_data = await service.create_api_key(api_key_create, user_id)
    return key_data


@router.patch(
    "/{user_id}/keys/{key_id}",
    response_model=APIKeyRead,
    dependencies=[Depends(current_superuser)],
    tags=["api_keys"],
)
async def update_api_key_for_user(
    user_id: ULID, key_id: str, api_key_update: APIKeyUpdate, service: APIKeyServiceDep
):
    return await service.update_api_key(key_id, api_key_update, user_id)


# --- User API Keys Revocation ---


@router.post(
    "/{user_id}/keys/{key_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
    tags=["api_keys"],
)
async def revoke_user_api_key(user_id: ULID, key_id: str, service: APIKeyServiceDep):
    await service.revoke_api_key(key_id, user_id)


@router.post(
    "/{user_id}/keys/revoke-all",
    response_model=RevokedAPIKeys,
    dependencies=[Depends(current_superuser)],
    tags=["api_keys"],
)
async def revoke_user_all_api_keys(user_id: ULID, service: APIKeyServiceDep):
    revoked_count = await service.revoke_user_all_api_keys(user_id)
    return {"user_id": user_id, "number_of_revoked_api_keys": revoked_count}
