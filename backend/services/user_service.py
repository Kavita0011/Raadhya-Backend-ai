# backend/services/user_service.py

import uuid
from typing import Optional
import logging

from backend.repositories.user_repository import UserRepository
from backend.models import User
from backend.schemas import UserResponse

logger = logging.getLogger(__name__)

class UserService:
    """
    Handles business logic related to user profiles.
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        logger.debug("UserService initialized.")

    async def get_user_profile(self, user_id: uuid.UUID) -> Optional[UserResponse]:
        """
        Retrieves a user's profile by ID.
        """
        user = await self.user_repo.get_user_by_id(user_id)
        if user:
            logger.info(f"Retrieved profile for user ID: {user_id}")
            return UserResponse.model_validate(user)
        logger.warning(f"User profile not found for ID: {user_id}")
        return None

    # You can add more user-specific business logic here, e.g.,
    # async def update_user_profile(self, user_id: uuid.UUID, update_data: UserUpdateSchema): ...
    # async def deactivate_user(self, user_id: uuid.UUID): ...