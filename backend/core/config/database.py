from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from core.config.settings import settings
import logging
import os

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
    """Initialize database tables if they do not exist.

    Local development environments often start with an empty database, so
    we create the schema automatically before any seeding happens. In
    production, deployment scripts should still run Alembic migrations
    before starting the app.
    """
    try:
        def has_tables(sync_conn):
            from sqlalchemy import inspect
            return bool(inspect(sync_conn).get_table_names())

        async with engine.begin() as conn:
            if not await conn.run_sync(has_tables):
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Created missing database tables")
    except Exception as e:
        logger.warning(f"Database schema initialization note: {e}")
        if settings.is_production_like:
            raise

        # Auto-seed if database has no users
        # Seed demo data only in development.
        # Never automatically create demo accounts in staging/production.
        if settings.ENVIRONMENT == "development":
            try:
                from database.seeders.users import seed_users

                async with async_session_maker() as session:
                    from sqlalchemy import select, func
                    from modules.users.models import User

                    count_res = await session.execute(
                        select(func.count(User.id))
                    )
                    count = count_res.scalar_one_or_none() or 0

                    demo_password = os.getenv("DEMO_USER_PASSWORD")
                    if count == 0 and demo_password:
                        await seed_users(session, demo_password)
                        logger.info(
                            "Development database initialized with demo users"
                        )

            except Exception as e:
                logger.warning(f"Development auto-seed note: {e}")
async def drop_db():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
