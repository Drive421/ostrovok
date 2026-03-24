from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.posts import PostCreate, PostPatch
from database.models import Post


class PostNotFoundError(Exception):
    pass


class PostsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_post(self, payload: PostCreate) -> Post:
        post = Post(title=payload.title, content=payload.content)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_post(self, post_id: UUID) -> Post:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError()
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
        return post

    async def delete_post(self, post_id: UUID) -> None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError()

        await self.session.delete(post)
        await self.session.commit()