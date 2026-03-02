"""
Database session configuration for TaskMaster Pro.
Provides async engine and session factory.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
#from sqlalchemy.pool import NullPool

from app.core.config import settings


if settings.DEBUG:
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
    )
else:
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
    )


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:
    """
    Get a database session.
    
    Returns:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        return session


async def close_db_connections() -> None:
    """Close all database connections."""
    await engine.dispose()


async def init_db() -> None:
    """
    Initialize database tables.
    Note: In production, use Alembic migrations instead.
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables.
    Warning: Only use in development/testing!
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
