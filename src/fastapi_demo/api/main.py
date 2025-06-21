from typing import Annotated

from fastapi import APIRouter, Depends

from fastapi_demo.api.routes import auth, users, utils
from fastapi_demo.core.auth.users import current_superuser, current_verified_active_user
from fastapi_demo.core.models.users import User

api_router = APIRouter()
api_router.include_router(utils.router)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router)


# NOTE: These routes serve no real purpose except for testing protected routes
@api_router.get("/authenticated-route", tags=["divers"])
async def authenticated_route(user: Annotated[User, Depends(current_verified_active_user)]):
    return {"message": f"Hello {user.email}!"}


@api_router.get("/protected-route", dependencies=[Depends(current_superuser)], tags=["divers"])
async def protected_route():
    return {"message": "Hello admin!"}
