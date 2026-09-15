"""Database Seeders for Development"""

from sqlalchemy.ext.asyncio import AsyncSession
from modules.users.models import User
from core.config.security import hash_password
import uuid


async def seed_users(db: AsyncSession):
    """Seed sample users"""
    
    users = [
        User(
            id=uuid.uuid4(),
            email="student@example.com",
            username="student",
            password_hash=hash_password("password123"),
            first_name="John",
            last_name="Student",
            role="student",
            college="IIT Delhi",
            is_active=True,
            email_verified=True
        ),
        User(
            id=uuid.uuid4(),
            email="mentor@example.com",
            username="mentor",
            password_hash=hash_password("password123"),
            first_name="Jane",
            last_name="Mentor",
            role="peer_mentor",
            college="IIT Delhi",
            is_mentor=True,
            mentor_hourly_rate=500.0,
            mentor_expertise=["Python", "Web Development", "Machine Learning"],
            mentor_verified=True,
            mentor_rating=4.8,
            is_active=True,
            email_verified=True
        ),
        User(
            id=uuid.uuid4(),
            email="professor@example.com",
            username="professor",
            password_hash=hash_password("password123"),
            first_name="Dr.",
            last_name="Professor",
            role="professor",
            college="IIT Delhi",
            is_mentor=True,
            mentor_expertise=["Data Science", "Research"],
            mentor_verified=True,
            is_active=True,
            email_verified=True
        )
    ]
    
    for user in users:
        db.add(user)
    
    await db.commit()
    
    return users
