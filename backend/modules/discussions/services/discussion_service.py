"""Discussion Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import Post, Comment, User
from core.config.logging import logger


class DiscussionService:
    """Discussion Management Service"""
    
    @staticmethod
    async def create_comment(
        post_id: str,
        author_id: str,
        content: str,
        db: AsyncSession
    ) -> Comment:
        """Create comment on post"""
        
        import uuid
        comment = Comment(
            id=uuid.uuid4(),
            post_id=uuid.UUID(post_id),
            author_id=uuid.UUID(author_id),
            content=content
        )
        
        db.add(comment)
        
        # Update post comment count
        post_stmt = select(Post).where(Post.id == uuid.UUID(post_id))
        post_result = await db.execute(post_stmt)
        post = post_result.scalar_one_or_none()
        
        if post:
            post.comment_count += 1
        
        await db.commit()
        await db.refresh(comment)
        
        logger.info(f"Comment created on post {post_id}")
        return comment
    
    @staticmethod
    async def upvote_post(post_id: str, user_id: str, db: AsyncSession) -> Post:
        """Upvote post"""
        
        import uuid
        post_stmt = select(Post).where(Post.id == uuid.UUID(post_id))
        post_result = await db.execute(post_stmt)
        post = post_result.scalar_one_or_none()
        
        if post:
            # Check if user already upvoted
            user_stmt = select(User).where(User.id == uuid.UUID(user_id))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user not in post.upvoted_by:
                post.upvoted_by.append(user)
                post.upvote_count += 1
                
                await db.commit()
                await db.refresh(post)
        
        return post
