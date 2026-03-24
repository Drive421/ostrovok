import pytest
from redis.asyncio import Redis

from app.core.config import settings


def _cache_key(post_id: str) -> str:
    return f"post:{post_id}"


@pytest.mark.asyncio
async def test_get_populates_cache(client):

    # Создём пост
    create_resp = await client.post("/posts", json={"title": "t1", "content": "c1"})
    assert create_resp.status_code == 201
    post = create_resp.json()
    post_id = post["id"]

    # Создаём соединение с Redis
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = _cache_key(post_id)

    # Удаляем ключ кеша
    await redis_client.delete(key)

    # Делаем первый запрос в БД
    first_get = await client.get(f"/posts/{post_id}")
    assert first_get.status_code == 200

    # Проверяем, что пост есть в кеше
    cached = await redis_client.get(key)
    assert cached is not None

    # Закрываем соединение с Redis
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_patch_invalidates_cache(client):

    # Создём пост
    create_resp = await client.post("/posts", json={"title": "t2", "content": "c2"})
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    # Создаём соединение с Redis
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = _cache_key(post_id)

    # Делаем первый запрос в БД
    get_resp = await client.get(f"/posts/{post_id}")
    assert get_resp.status_code == 200

    # Проверяем, что пост есть в кеше
    assert await redis_client.get(key) is not None

    # Делаем patch запрос
    patch_resp = await client.patch(f"/posts/{post_id}", json={"title": "t2-new"})
    assert patch_resp.status_code == 200

    # Проверяем кэш удалён
    assert await redis_client.get(key) is None

    # Закрываем соединение с Redis
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_delete_invalidates_cache(client):

    # Создём пост
    create_resp = await client.post("/posts", json={"title": "t3", "content": "c3"})
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    # Создаём соединение с Redis
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = _cache_key(post_id)

    # Делаем первый запрос в БД
    get_resp = await client.get(f"/posts/{post_id}")
    assert get_resp.status_code == 200

    # Проверяем, что пост есть в кеше
    assert await redis_client.get(key) is not None

    # Делаем delete запрос
    del_resp = await client.delete(f"/posts/{post_id}")
    assert del_resp.status_code == 204

    # Проверяем, что кэш удалён
    assert await redis_client.get(key) is None

    # Делаем запрос на получение поста после удаления и проверяем, что пост не найден (404)
    get_after_delete = await client.get(f"/posts/{post_id}")
    assert get_after_delete.status_code == 404

    # Закрываем соединение с Redis
    await redis_client.aclose()