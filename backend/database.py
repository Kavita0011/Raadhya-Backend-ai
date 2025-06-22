# backend/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# Base for declarative models
Base = declarative_base()

# Async SQLAlchemy Engine
# pool_size: The number of connections to keep open in the pool.
# max_overflow: The number of connections that can be opened beyond the pool_size.
# pool_timeout: The number of seconds to wait before giving up on getting a connection from the pool.
# pool_recycle: The number of seconds after which a connection is automatically recycled.
#               Useful for preventing stale connections (e.g., after database restarts).
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Set to True to log SQL statements for debugging
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600, # Recycle connections after 1 hour
)

# Async Session Maker
# expire_on_commit=False: Prevents objects from being detached after commit,
#                         allowing access to attributes without re-fetching.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """
    Initializes the database by creating all tables defined in Base.
    This is typically run once or via Alembic migrations.
    """
    async with async_engine.begin() as conn:
        # Check if tables already exist (optional, migrations handle this in production)
        # For first run without alembic auto-generate, this will create tables.
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables checked/created.")

def get_async_session_maker():
    """
    Returns the async session maker for direct use.
    """
    return AsyncSessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an asynchronous database session.
    It yields a session and ensures it is closed after the request.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        await session.rollback()
        raise # Re-raise the exception
    finally:
        await session.close()

# For Alembic configuration (alembic/env.py will import this Base and async_engine)
# ensure this module is importable by Alembic