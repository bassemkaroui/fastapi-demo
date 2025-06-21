from typing import Annotated

from fastapi import Depends, Query
from sqlmodel import select

from fastapi_demo.api.dependencies import SessionDep
from fastapi_demo.core.auth.users import current_superuser, fastapi_users
from fastapi_demo.core.models.users import User
from fastapi_demo.core.schemas.base import PaginationParams
from fastapi_demo.core.schemas.users import UserRead, UserUpdate

router = fastapi_users.get_users_router(UserRead, UserUpdate)


@router.get("/", response_model=list[UserRead], dependencies=[Depends(current_superuser)])
async def read_all_users(query_params: Annotated[PaginationParams, Query()], session: SessionDep):
    statement = select(User).offset(query_params.offset).limit(query_params.limit)
    query_result = await session.exec(statement)
    users = query_result.unique().all()
    return users
