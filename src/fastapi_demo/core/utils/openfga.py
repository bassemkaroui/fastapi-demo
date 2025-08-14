import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from openfga_sdk import ClientConfiguration, CreateStoreRequest, ListStoresResponse, OpenFgaClient
from openfga_sdk.credentials import CredentialConfiguration, Credentials

from fastapi_demo.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_openfga_client(
    api_url: str,
    auth_method: str | None = None,
    store_id: str | None = None,
    authorization_model_id: str | None = None,
) -> AsyncGenerator[OpenFgaClient]:
    credentials = None
    if auth_method == "preshared":
        credentials = Credentials(
            method="api_token",
            configuration=CredentialConfiguration(api_token=settings.FGA_API_TOKEN),
        )

    configuration = ClientConfiguration(
        api_url=api_url.rstrip("/"),
        store_id=store_id,
        authorization_model_id=authorization_model_id,
        credentials=credentials,
    )
    async with OpenFgaClient(configuration) as fga_client:
        yield fga_client


async def get_store_by_name(fga_client: OpenFgaClient, name: str) -> ListStoresResponse:
    return await fga_client.list_stores(options={"name": name})


async def create_store(name: str | None = None) -> None:
    store_name = name or settings.FGA_STORE_NAME

    async with create_openfga_client(
        api_url=str(settings.FGA_API_URL), auth_method=settings.OPENFGA_AUTHN_METHOD
    ) as fga_client:
        existing = await get_store_by_name(fga_client, name=store_name)
        if existing.stores:
            logger.warning(f"A store with the name '{store_name}' already exists")
            return

        body = CreateStoreRequest(name=store_name)
        response = await fga_client.create_store(body)
        logger.info(f"Store '{store_name}' with the ID '{response.id}' was created.")


async def get_store_id() -> str | None:
    if settings.FGA_STORE_ID:
        return settings.FGA_STORE_ID

    async with create_openfga_client(
        api_url=str(settings.FGA_API_URL), auth_method=settings.OPENFGA_AUTHN_METHOD
    ) as fga_client:
        existing = await get_store_by_name(fga_client, name=settings.FGA_STORE_NAME)

    if not existing.stores:
        return None
    return existing.stores[0].id  # type: ignore[no-any-return]


async def get_authorization_model_id(store_id: str) -> str | None:
    if settings.FGA_MODEL_ID:
        return settings.FGA_MODEL_ID

    async with create_openfga_client(
        api_url=str(settings.FGA_API_URL),
        auth_method=settings.OPENFGA_AUTHN_METHOD,
        store_id=store_id,
    ) as fga_client:
        response = await fga_client.read_latest_authorization_model()

    return response.authorization_model.id if response.authorization_model else None
