# backend/repositories/session_repository.py

import uuid
from typing import Optional
import logging

from backend.schemas import SessionData
from backend.security.auth_manager import create_session as create_redis_session, \
                                          get_session as get_redis_session, \
                                          delete_session as delete_redis_session

logger = logging.getLogger(__name__)

class SessionRepository:
    """
    Handles all operations related to session data stored in Redis.
    This acts as an abstraction layer over the direct Redis client operations
    defined in auth_manager.
    """
    def __init__(self):
        logger.debug("SessionRepository initialized.")

    async def create_session_record(self, user_id: uuid.UUID, csrf_token: str) -> SessionData:
        """
        Creates and stores a new session record in Redis.
        """
        return await create_redis_session(user_id, csrf_token)

    async def get_session_record(self, session_id: uuid.UUID) -> Optional[SessionData]:
        """
        Retrieves a session record from Redis.
        """
        return await get_redis_session(session_id)

    async def delete_session_record(self, session_id: uuid.UUID) -> None:
        """
        Deletes a session record from Redis.
        """
        await delete_redis_session(session_id)