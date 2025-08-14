import asyncio
import os

from fastapi_demo.core.config import settings
from fastapi_demo.core.utils.openfga import create_store

tests_store_name = os.getenv("FGA_TESTS_STORE_NAME", "")


async def main():
    await create_store(name=settings.FGA_STORE_NAME)
    # await create_store(name=tests_store_name)


if __name__ == "__main__":
    asyncio.run(main())
