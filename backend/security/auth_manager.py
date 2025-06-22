# backend/security/auth_manager.py

import redis.asyncio as redis
import uuid
from datetime import datetime, timedelta, timezone
import json
import logging

from backend.config import settings
from backend.schemas import SessionData
from backend.exceptions.custom_exceptions import SessionExpiredException

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client: redis.Redis = None

async def init_redis_connection():
    """
    Initializes the asynchronous Redis client connection.
    This should be called during application startup.
    """
    global redis_client
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None,
            decode_responses=False # Keep as bytes, we'll encode/decode manually
        )
        await redis_client.ping() # Test connection
        logger.info("Redis client initialized and connected successfully.")
    except Exception as e:
        logger.critical(f"Failed to connect to Redis: {e}", exc_info=True)
        raise # Re-raise to prevent app from starting without Redis

async def close_redis_connection():
    """
    Closes the Redis client connection.
    This should be called during application shutdown.
    """
    if redis_client:
        await redis_client.close()
        logger.info("Redis client connection closed.")

async def create_session(user_id: uuid.UUID, csrf_token: str) -> SessionData:
    """
    Creates a new session, stores it in Redis, and returns the session data.
    """
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.SESSION_ABSOLUTE_TIMEOUT)
    idle_expires_at = now + timedelta(seconds=settings.SESSION_IDLE_TIMEOUT)

    session_data = SessionData(
        session_id=session_id,
        user_id=user_id,
        csrf_token=csrf_token,
        created_at=now,
        expires_at=expires_at,
        last_activity_at=now
    )

    try:
        # Store the session data as JSON string
        session_key = str(session_id)
        session_json = session_data.model_dump_json() # Use model_dump_json for Pydantic v2+

        # Set the session in Redis with the idle timeout
        await redis_client.setex(session_key, settings.SESSION_IDLE_TIMEOUT, session_json)
        logger.info(f"Session {session_id} created and stored in Redis for user {user_id}.")
        return session_data
    except Exception as e:
        logger.error(f"Error creating session for user {user_id}: {e}", exc_info=True)
        raise

async def get_session(session_id: uuid.UUID) -> Optional[SessionData]:
    """
    Retrieves session data from Redis. Also handles session expiry logic.
    If session is found and valid, it updates last_activity_at and extends idle timeout.
    """
    session_key = str(session_id)
    try:
        session_json = await redis_client.get(session_key)
        if not session_json:
            logger.debug(f"Session {session_id} not found in Redis.")
            return None

        session_data = SessionData.model_validate_json(session_json) # Use model_validate_json for Pydantic v2+

        now = datetime.now(timezone.utc)

        # Check absolute expiration
        if session_data.expires_at < now:
            logger.warning(f"Session {session_id} for user {session_data.user_id} expired (absolute).")
            await delete_session(session_id) # Clean up expired session
            raise SessionExpiredException(detail="Session has expired.")

        # Check idle expiration (Redis's TTL mechanism handles this implicitly for `setex`)
        # If we reached here, Redis already considered it active based on `setex`.
        # Now, update last_activity_at and extend idle timeout for next request.
        session_data.last_activity_at = now
        await redis_client.setex(session_key, settings.SESSION_IDLE_TIMEOUT, session_data.model_dump_json())
        logger.debug(f"Session {session_id} refreshed for user {session_data.user_id}.")
        return session_data

    except SessionExpiredException:
        raise # Re-raise if already caught and specific exception is desired
    except Exception as e:
        logger.error(f"Error retrieving or updating session {session_id}: {e}", exc_info=True)
        return None

async def delete_session(session_id: uuid.UUID) -> None:
    """
    Deletes a session from Redis.
    """
    session_key = str(session_id)
    try:
        deleted_count = await redis_client.delete(session_key)
        if deleted_count > 0:
            logger.info(f"Session {session_id} deleted from Redis.")
        else:
            logger.debug(f"Attempted to delete non-existent session {session_id}.")
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise

# Initialize Redis connection when this module is imported (will be called in main.py lifespan)
# This is a placeholder for the lifespan event in main.py
# await init_redis_connection()