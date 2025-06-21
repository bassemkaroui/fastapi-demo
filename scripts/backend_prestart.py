import asyncio
import logging

from sqlalchemy import select

# from sqlmodel import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from fastapi_demo.core.db import async_session_maker

# from fastapi_demo.core.db import async_sqlmodel_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WAIT_SECONDS = 1
MAX_TRIES = 60 * 5  # 5 minutes


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
    reraise=True,
)
async def init() -> None:
    try:
        async with async_session_maker() as session:
            await session.execute(select(1))
        # async with async_sqlmodel_session_maker() as session:
        #     await session.exec(select(1))
    except Exception:
        logger.exception("The Database is not ready yet")
        raise


async def main() -> None:
    logger.info("Initializing service")
    await init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    asyncio.run(main())
