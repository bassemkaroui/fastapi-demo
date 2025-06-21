import uuid

from fastapi_users import FastAPIUsers

from fastapi_demo.core.auth.backends import redis_auth_backend
from fastapi_demo.core.auth.manager import get_user_manager
from fastapi_demo.core.models.users import User

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [redis_auth_backend],
    # get_user_manager, [redis_auth_backend, jwt_auth_backend]
)
current_verified_active_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, verified=True, superuser=True)
