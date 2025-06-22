# backend/repositories/user_repository.py

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import logging

from backend.models import User
from backend.schemas import UserCreate, UserInDB

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Handles all database operations related to the User model.
    """
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        logger.debug("UserRepository initialized.")

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """
        Creates a new user record in the database.
        """
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        logger.info(f"User '{db_user.username}' (ID: {db_user.id}) created successfully.")
        return db_user

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieves a user by their UUID.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.debug(f"User with ID {user_id} found.")
        else:
            logger.debug(f"User with ID {user_id} not found.")
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by their username.
        """
        stmt = select(User).where(User.username == username)
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.debug(f"User with username '{username}' found.")
        else:
            logger.debug(f"User with username '{username}' not found.")
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a user by their email address.
        """
        stmt = select(User).where(User.email == email)
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.debug(f"User with email '{email}' found.")
        else:
            logger.debug(f"User with email '{email}' not found.")
        return user

    async def get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """
        Retrieves a user by either their username or email address.
        """
        stmt = select(User).where(or_(User.username == identifier, User.email == identifier))
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.debug(f"User with identifier '{identifier}' found.")
        else:
            logger.debug(f"User with identifier '{identifier}' not found.")
        return user

    # You can add more CRUD methods here: update_user, delete_user, etc.