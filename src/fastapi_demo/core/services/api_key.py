import secrets
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from asyncpg import UniqueViolationError
from fastapi_pagination.ext.sqlmodel import apaginate
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, desc, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from ulid import ULID

from fastapi_demo.core.config import Settings
from fastapi_demo.core.exceptions import APIKeyNotFoundOrRevokedError, UserNotFoundError
from fastapi_demo.core.models.users import APIKey, User
from fastapi_demo.core.schemas.api_keys import APIKeyCreateRequest, APIKeyUpdate


class APIKeyService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.hasher = Argon2Hasher()
        self.redis = aioredis.from_url(
            str(settings.REDIS_URI), decode_responses=True, db=settings.REDIS_USERS_DB
        )
        self.key_prefix = settings.REDIS_USERS_APIKEY_KEY_PREFIX

    async def create_api_key(
        self, api_key_create: APIKeyCreateRequest, owner_id: ULID, *, verify_user: bool = True
    ) -> dict[str, Any]:
        if verify_user:
            user = await self.session.get(User, owner_id)
            if not user:
                raise UserNotFoundError(owner_id)

        while True:
            key_id = f"fastapi-demo-{secrets.token_urlsafe(16)}"
            key_secret = secrets.token_urlsafe(32)
            hashed_key = self.hasher.hash(key_secret)
            key_preview = f"fastapi-demo-...{key_secret[-4:]}"
            name = api_key_create.name
            db_key = APIKey(
                key_id=key_id,
                key_hash=hashed_key,
                key_preview=key_preview,
                owner_id=owner_id,
                name=name,
            )

            self.session.add(db_key)
            try:
                await self.session.commit()
                await self.session.refresh(db_key)
                break
            except IntegrityError as exc:
                # print(str(exc))
                await self.session.rollback()
                is_unique = isinstance(exc.orig, UniqueViolationError)
                if is_unique:
                    # key_id collision
                    continue
                raise
        return {
            "api_key": f"{key_id}.{key_secret}",
            "key_id": key_id,
            "key_preview": key_preview,
            "name": name,
            "created_at": db_key.created_at,
        }

    async def read_user_all_api_keys(  # type: ignore[no-untyped-def]
        self,
        owner_id: ULID,
        *,
        search: str | None = None,
        verify_user: bool = True,
    ):
        if verify_user:
            user = await self.session.get(User, owner_id)
            if not user:
                raise UserNotFoundError(owner_id)

        statement = select(APIKey).where(APIKey.owner_id == owner_id).where(APIKey.revoked == False)  # noqa: E712

        if search is not None:
            pattern = f"%{search}%"
            statement = statement.where(col(APIKey.name).ilike(pattern))
        # query_result = await self.session.exec(statement)
        # api_keys = query_result.all()
        page = await apaginate(
            self.session,
            statement.order_by(desc(APIKey.id)),  # type: ignore[arg-type]
            count_query=select(func.count()).select_from(APIKey),
        )
        return page

    async def update_api_key(
        self,
        api_key_id: str,
        api_key_update: APIKeyUpdate,
        user_id: ULID | None = None,
        *,
        verify_user: bool = True,
    ) -> APIKey:
        statement = select(APIKey).where(APIKey.key_id == api_key_id).where(APIKey.revoked == False)  # noqa: E712
        if user_id:
            if verify_user:
                owner = await self.session.get(User, user_id)
                if not owner:
                    raise UserNotFoundError(user_id=user_id)
            statement = statement.where(APIKey.owner_id == user_id)

        query_result = await self.session.exec(statement)
        db_key = query_result.first()
        if not db_key:
            raise APIKeyNotFoundOrRevokedError(api_key_id)

        updated_data = api_key_update.model_dump(exclude_unset=True)
        db_key.sqlmodel_update(updated_data, update={"updated_at": datetime.now(timezone.utc)})

        self.session.add(db_key)
        await self.session.commit()
        # await self.session.refresh(db_key)
        await self.redis.delete(f"{self.key_prefix}{api_key_id}")

        return db_key

    async def revoke_api_key(
        self, api_key_id: str, user_id: ULID | None = None, *, verify_user: bool = True
    ) -> None:
        statement = select(APIKey).where(APIKey.key_id == api_key_id).where(APIKey.revoked == False)  # noqa: E712
        if user_id:
            if verify_user:
                user = await self.session.get(User, user_id)
                if not user:
                    raise UserNotFoundError(user_id)
            statement = statement.where(APIKey.owner_id == user_id)

        query_result = await self.session.exec(statement)
        key_entry = query_result.first()
        if not key_entry:
            raise APIKeyNotFoundOrRevokedError(api_key_id)

        key_entry.revoked = True
        self.session.add(key_entry)
        await self.session.commit()
        await self.redis.delete(f"{self.key_prefix}{api_key_id}")

    async def revoke_user_all_api_keys(self, owner_id: ULID, *, verify_user: bool = True) -> int:
        if verify_user:
            user = await self.session.get(User, owner_id)
            if not user:
                raise UserNotFoundError(owner_id)

        update_statement = (
            update(APIKey)
            .where(APIKey.owner_id == owner_id)  # type: ignore[arg-type]
            .where(APIKey.revoked == False)  # type: ignore[arg-type] # noqa: E712
            .values(revoked=True)
            # keep the session in sync with what we updated
            .execution_options(synchronize_session="fetch")
        )
        api_key_ids_statement = (
            select(APIKey.key_id).where(APIKey.owner_id == owner_id).where(APIKey.revoked == False)  # noqa: E712
        )

        result = await self.session.exec(api_key_ids_statement)
        api_key_ids = result.all()
        update_result = await self.session.exec(update_statement)  # type: ignore[call-overload]
        await self.session.commit()

        if api_key_ids:
            redis_keys = [f"{self.key_prefix}{key_id}" for key_id in api_key_ids]
            await self.redis.unlink(*redis_keys)
        return update_result.rowcount or 0
