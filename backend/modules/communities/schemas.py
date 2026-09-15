"""Community Schemas"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class CommunityCreate(BaseModel):
    """Create community request"""
    name: str
    description: str
    community_type: str
    thumbnail: Optional[str] = None


class CommunityResponse(BaseModel):
    """Community response"""
    id: uuid.UUID
    name: str
    description: str
    community_type: str
    creator_id: uuid.UUID
    members_count: int
    posts_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    """Create post request"""
    title: str
    content: str


class PostResponse(BaseModel):
    """Post response"""
    id: uuid.UUID
    title: str
    content: str
    author_id: uuid.UUID
    upvote_count: int
    comment_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    """Create comment request"""
    content: str


class CommentResponse(BaseModel):
    """Comment response"""
    id: uuid.UUID
    content: str
    author_id: uuid.UUID
    upvote_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
