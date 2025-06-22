from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from backend.config import settings
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Base for declarative models
Base = declarative_base()

# Ensure settings.DATABASE_URL uses "postgresql+asyncpg://"
# Example: postgresql+asyncpg://user:pass@host:port/db
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to True to log SQL statements for debugging
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Async Session Maker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """
    Initializes the database by creating all tables defined in Base.
    Run this once or via Alembic migrations.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables checked/created.")

def get_async_session_maker():
    """
    Returns the async session maker for direct use.
    """
    return AsyncSessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an async database session.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        await session.rollback()
        raise
    finally:
        await session.close()
