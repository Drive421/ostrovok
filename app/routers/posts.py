from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.posts import PostCreate, PostPatch, PostResponse
from app.services.posts_service import PostNotFoundError, PostsService
from database.session import get_session

from app.services.redis_cache import RedisCache

router = APIRouter(prefix="/posts", tags=["posts"])


def get_posts_service(session: AsyncSession = Depends(get_session)) -> PostsService:
    return PostsService(session=session)

def get_posts_service(session: AsyncSession = Depends(get_session)) -> PostsService:
    return PostsService(session=session, cache=RedisCache())
    

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    service: PostsService = Depends(get_posts_service),
) -> PostResponse:
    post = await service.create_post(payload)
    return PostResponse.model_validate(post)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    service: PostsService = Depends(get_posts_service),
) -> PostResponse:
    try:
        post = await service.get_post(post_id)
        return PostResponse.model_validate(post)
    except PostNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@router.patch("/{post_id}", response_model=PostResponse)
async def patch_post(
    post_id: UUID,
    payload: PostPatch,
    service: PostsService = Depends(get_posts_service),
) -> PostResponse:
    try:
        post = await service.update_post(post_id, payload)
        return PostResponse.model_validate(post)
    except PostNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    service: PostsService = Depends(get_posts_service),
) -> None:
    try:
        await service.delete_post(post_id)
    except PostNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")