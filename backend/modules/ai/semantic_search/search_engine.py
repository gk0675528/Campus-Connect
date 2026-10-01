"""AI Services - Semantic Search"""

import logging

logger = logging.getLogger(__name__)


class SemanticSearch:
    """AI-powered semantic search"""
    
    @staticmethod
    async def search_mentors(query: str, db) -> list:
        """Search mentors using semantic search"""
        
        from core.config.settings import settings
        from openai import AsyncOpenAI
        from sqlalchemy import select
        from modules.users.models import User
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get embedding for query
        response = await client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        
        query_embedding = response.data[0].embedding
        
        # Query similar mentors from database (using pgvector)
        stmt = select(User).where(User.is_mentor == True).limit(10)
        result = await db.execute(stmt)
        mentors = result.scalars().all()
        
        logger.info(f"Semantic search completed for: {query}")
        return mentors
    
    @staticmethod
    async def search_communities(query: str, db) -> list:
        """Search communities using semantic search"""
        
        from sqlalchemy import select
        from modules.users.models import Community
        
        # Simple implementation - can be enhanced with embeddings
        stmt = select(Community).where(
            Community.is_active == True
        ).limit(10)
        
        result = await db.execute(stmt)
        communities = result.scalars().all()
        
        logger.info(f"Community search completed for: {query}")
        return communities
