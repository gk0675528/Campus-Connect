"""Profile Model"""

from sqlalchemy import Column, String, Uuid, ForeignKey, Text, JSON, DateTime, Integer, Float
from core.config.database import Base
from datetime import datetime
import uuid


class Profile(Base):
    """Extended User Profile Model"""
    __tablename__ = "profiles"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal
    bio = Column(Text, nullable=True)
    profile_photo = Column(String(500), nullable=True)
    cover_photo = Column(String(500), nullable=True)
    
    # Education
    college = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    # Professional
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    years_experience = Column(Integer, nullable=True)
    
    # Skills & Interests
    skills = Column(JSON, default=list, nullable=True)
    interests = Column(JSON, default=list, nullable=True)
    languages = Column(JSON, default=list, nullable=True)
    
    # Social
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    
    # Preferences
    notification_preferences = Column(Text, nullable=True)  # JSON string
    privacy_settings = Column(Text, nullable=True)  # JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

