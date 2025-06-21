import asyncio

from sqlmodel import select

from fastapi_demo.core.db import async_sqlmodel_session_maker
from fastapi_demo.core.models.users import User


async def main():
    async with async_sqlmodel_session_maker() as session:
        query_result = await session.exec(select(User))
        users = query_result.unique().all()
        for user in users:
            if user.full_name:
                parts = user.full_name.strip().split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else None
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
