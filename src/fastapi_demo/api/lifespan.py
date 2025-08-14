from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from openfga_sdk import OpenFgaClient
from pydantic import BaseModel, ConfigDict
from sqlakeyset import custom_bookmark_type
from ulid import ULID

from fastapi_demo.core.config import settings
from fastapi_demo.core.utils.openfga import (
    create_openfga_client,
    get_authorization_model_id,
    get_store_id,
)


def _ulid_serialize(value: ULID) -> str:
    return str(value)


def _ulid_unserialize(value: str) -> ULID:
    return ULID.from_str(value)  # type: ignore[no-any-return]


class AppState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    http_client: AsyncClient
    store_id: str
    authorization_model_id: str
    fga_client: OpenFgaClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict[str, Any]]:  # noqa: ARG001
    custom_bookmark_type(ULID, "ulid", _ulid_unserialize, _ulid_serialize)

    # OpenFGA
    store_id = await get_store_id()
    if not store_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No OpenFGA Store was found."
        )
    authorization_model_id = await get_authorization_model_id(store_id)
    if not authorization_model_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No authorization model was found for the store '{store_id}'.",
        )

    print(f"{store_id=}")
    print(f"{authorization_model_id=}")
    async with (
        AsyncClient() as http_client,
        create_openfga_client(
            api_url=str(settings.FGA_API_URL),
            auth_method=settings.OPENFGA_AUTHN_METHOD,
            store_id=store_id,
            authorization_model_id=authorization_model_id,
        ) as fga_client,
    ):
        yield {
            "http_client": http_client,
            "store_id": store_id,
            "authorization_model_id": authorization_model_id,
            "fga_client": fga_client,
        }
