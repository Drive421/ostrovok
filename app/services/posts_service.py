from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.posts import PostCreate, PostPatch
from database.models import Post

from app.core.config import settings
from app.services.redis_cache import RedisCache


class PostNotFoundError(Exception):
    pass


class PostsService:

    def __init__(self, session: AsyncSession, cache: RedisCache) -> None:
        self.session = session
        self.cache = cache


    @staticmethod
    def _cache_key(post_id: UUID) -> str:
        return f"post:{post_id}"


    async def create_post(self, payload: PostCreate) -> Post:
        post = Post(title=payload.title, content=payload.content)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post


    async def get_post(self, post_id: UUID) -> Post:
        
        cache_key = self._cache_key(post_id)

        cached = await self.cache.get_json(cache_key)
        if cached is not None:
            return Post(
                id=cached["id"],
                title=cached["title"],
                content=cached["content"],
                created_at=cached["created_at"],
                updated_at=cached["updated_at"],
            )
        
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError()

        await self.cache.set_json(
            cache_key, 
            {
                "id": str(post.id),
                "title": post.title,
                "content": post.content,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
            },
            ttl=settings.cache_ttl_seconds
            )

        return post


    async def update_post(self, post_id: UUID, payload: PostPatch) -> Post:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError()

        if payload.title is not None:
            post.title = payload.title
        if payload.content is not None:
            post.content = payload.content

        await self.session.commit()
        await self.session.refresh(post)
        await self.cache.delete(self._cache_key(post_id))

        return post


    async def delete_post(self, post_id: UUID) -> None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError()

        await self.session.delete(post)
        await self.session.commit()
        await self.cache.delete(self._cache_key(post_id))