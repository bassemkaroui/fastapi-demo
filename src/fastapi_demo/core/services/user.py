from fastapi_pagination.ext.sqlmodel import apaginate
from sqlmodel import col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_demo.core.models.users import User


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def read_all_users(  # type: ignore[no-untyped-def]
        self,
        *,
        is_active: bool | None = None,
        is_verified: bool | None = None,
        is_superuser: bool | None = None,
        search: str | None = None,
    ):
        statement = select(User)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        if is_verified is not None:
            statement = statement.where(User.is_verified == is_verified)
        if is_superuser is not None:
            statement = statement.where(User.is_superuser == is_superuser)
        if search is not None:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    col(User.first_name).ilike(pattern),
                    col(User.last_name).ilike(pattern),
                    col(User.email).ilike(pattern),
                )
            )
        # query_result = await self.session.exec(statement)
        # users = query_result.all()
        page = await apaginate(self.session, statement.order_by(User.id))  # type: ignore[arg-type]
        return page
