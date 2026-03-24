import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


class RedisCache:
    def __init__(self) -> None:
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: dict[str, Any], ttl: int) -> None:
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)