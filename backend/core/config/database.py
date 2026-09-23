from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from core.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Engine connect args for SQLite
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
    "future": True,
}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    if settings.DEBUG:
        engine_kwargs["poolclass"] = NullPool

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# Create session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


async def get_db():
    """Get database session dependency"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables and seed sample data if empty"""
    import modules.users.models  # noqa: F401
    import modules.profiles.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Auto-seed if database has no users
    try:
        from database.seeders.users import seed_users
        async with async_session_maker() as session:
            from sqlalchemy import select, func
            from modules.users.models import User
            count_res = await session.execute(select(func.count(User.id)))
            count = count_res.scalar_one_or_none() or 0
            if count == 0:
                await seed_users(session)
                logger.info("Initialized database with default test accounts and communities")
    except Exception as e:
        logger.warning(f"Auto-seed note: {e}")


async def drop_db():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

