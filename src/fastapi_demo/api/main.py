from fastapi import APIRouter, Depends

from fastapi_demo.api.dependencies import CurrentVerifiedActiveUserDep
from fastapi_demo.api.routes import auth, oauth, users, utils
from fastapi_demo.core.auth.users import current_superuser

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(oauth.router, prefix="/auth", tags=["oauth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router)


# NOTE: These routes serve no real purpose except for testing protected routes
@api_router.get("/authenticated-route", tags=["divers"])
async def authenticated_route(user: CurrentVerifiedActiveUserDep):
    return {"message": f"Hello {user.email}!"}


@api_router.get("/protected-route", dependencies=[Depends(current_superuser)], tags=["divers"])
async def protected_route():
    return {"message": "Hello admin!"}
