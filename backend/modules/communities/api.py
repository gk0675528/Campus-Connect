"""Community API Router"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.communities.services.community_service import CommunityService
from modules.communities.schemas import CommunityCreate, CommunityResponse, PostCreate, PostResponse
from modules.users.models import User, Post, Comment, Community, community_members
from sqlalchemy import select
import uuid

router = APIRouter(prefix="/communities", tags=["communities"])


@router.get("/", response_model=list[CommunityResponse])
async def list_communities(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """List communities"""
    from modules.users.models import Community
    stmt = select(Community).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    community_data: CommunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create community"""
    
    community = await CommunityService.create_community(
        name=community_data.name,
        description=community_data.description,
        community_type=community_data.community_type,
        creator_id=str(current_user.id),
        thumbnail=community_data.thumbnail,
        db=db
    )
    
    return community


@router.get("/{community_id}", response_model=CommunityResponse)
async def get_community(
    community_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get community"""
    
    community = await CommunityService.get_community(community_id, db)
    
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    return community


@router.post("/{community_id}/join")
async def join_community(
    community_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join community"""
    
    await CommunityService.join_community(
        community_id=community_id,
        user_id=str(current_user.id),
        db=db
    )
    
    return {"message": "Successfully joined community"}


@router.post("/{community_id}/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    community_id: str,
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create post in community"""
    
    community = await CommunityService.get_community(community_id, db)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    membership = await db.execute(
        select(community_members).where(
            community_members.c.community_id == uuid.UUID(community_id),
            community_members.c.user_id == current_user.id,
        )
    )
    if membership.first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Join the community before posting")

    post = Post(
        id=uuid.uuid4(),
        community_id=uuid.UUID(community_id),
        author_id=current_user.id,
        title=post_data.title,
        content=post_data.content
    )
    
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    return post


@router.get("/{community_id}/posts", response_model=list[PostResponse])
async def get_community_posts(
    community_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """Get community posts"""
    
    stmt = select(Post).where(Post.community_id == uuid.UUID(community_id)).limit(limit)
    result = await db.execute(stmt)
    
    return result.scalars().all()
