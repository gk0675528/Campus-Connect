"""Community Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from modules.users.models import Community, User
from core.exceptions.auth_exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class CommunityService:
    """Community Management Service"""
    
    @staticmethod
    async def create_community(
        name: str,
        description: str,
        community_type: str,
        creator_id: str,
        thumbnail: str = None,
        db: AsyncSession = None
    ) -> Community:
        """Create new community"""
        
        community = Community(
            name=name,
            description=description,
            community_type=community_type,
            creator_id=creator_id,
            thumbnail=thumbnail
        )
        
        db.add(community)
        await db.commit()
        await db.refresh(community)
        
        logger.info(f"Community created: {community.id}")
        return community
    
    @staticmethod
    async def get_community(community_id: str, db: AsyncSession) -> Community:
        """Get community"""
        stmt = select(Community).where(Community.id == community_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def join_community(
        community_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Community:
        """Join community"""
        
        community = await CommunityService.get_community(community_id, db)
        if not community:
            raise NotFoundError("Community not found")
        
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")
        
        if user not in community.members:
            community.members.append(user)
            community.members_count += 1
            
            await db.commit()
            await db.refresh(community)
        
        logger.info(f"User {user_id} joined community {community_id}")
        return community
    
    @staticmethod
    async def leave_community(
        community_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Community:
        """Leave community"""
        
        community = await CommunityService.get_community(community_id, db)
        if not community:
            raise NotFoundError("Community not found")
        
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")
        
        if user in community.members:
            community.members.remove(user)
            community.members_count -= 1
            
            await db.commit()
            await db.refresh(community)
        
        logger.info(f"User {user_id} left community {community_id}")
        return community
