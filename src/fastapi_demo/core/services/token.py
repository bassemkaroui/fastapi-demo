from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio.client import Redis
    from ulid import ULID


class TokenService:
    def __init__(self, redis_users_client: "Redis", redis_users_key_prefix: str):
        self.redis = redis_users_client
        self.redis_users_key_prefix = redis_users_key_prefix

    async def revoke(self, token: str) -> None:
        await self.redis.delete(f"{self.redis_users_key_prefix}{token}")

    async def revoke_all_for_user(self, user_id: "ULID") -> None:
        cursor = 0
        keys_to_delete: list[str] = []
        user_id_str = str(user_id)

        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor, match=f"{self.redis_users_key_prefix}*", count=100
            )
            if not keys:
                if cursor == 0:
                    break
                continue

            vals = await self.redis.mget(keys=keys)
            keys_to_delete.extend([
                key for key, val in zip(keys, vals, strict=True) if val == user_id_str
            ])

            if cursor == 0:
                break

        if keys_to_delete:
            await self.redis.unlink(*keys_to_delete)
