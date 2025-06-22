# backend/services/auth_service.py

import uuid
import logging
from typing import Optional

from backend.repositories.user_repository import UserRepository
from backend.repositories.session_repository import SessionRepository
from backend.security.password import hash_password, verify_password
from backend.security.csrf import generate_csrf_token
from backend.schemas import UserCreate, LoginRequest, UserResponse, SessionData
from backend.exceptions.custom_exceptions import (
    UserAlreadyExistsException, UserNotFoundException, IncorrectCredentialsException,
    UnauthorizedException
)
from backend.models import User # For type hinting

logger = logging.getLogger(__name__)

class AuthService:
    """
    Handles authentication-related business logic: user registration, login, logout,
    and session management.
    """
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
        logger.debug("AuthService initialized.")

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Registers a new user after checking for existing username/email.
        """
        # Check if username or email already exists
        existing_user = await self.user_repo.get_user_by_username_or_email(user_data.username)
        if existing_user:
            logger.warning(f"Registration attempt with existing username: {user_data.username}")
            raise UserAlreadyExistsException(detail="Username or email already registered.")

        existing_user = await self.user_repo.get_user_by_username_or_email(user_data.email)
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise UserAlreadyExistsException(detail="Username or email already registered.")

        hashed_password = hash_password(user_data.password)
        new_user = await self.user_repo.create_user(user_data, hashed_password)
        logger.info(f"User '{new_user.username}' (ID: {new_user.id}) registered successfully.")
        return UserResponse.model_validate(new_user)

    async def login_user(self, login_data: LoginRequest) -> SessionData:
        """
        Authenticates a user and creates a new session upon successful login.
        Returns the SessionData to be used for setting cookies and CSRF token.
        """
        user = await self.user_repo.get_user_by_username_or_email(login_data.username_or_email)

        if not user or not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Login failed for identifier: {login_data.username_or_email} - Invalid credentials.")
            raise IncorrectCredentialsException(detail="Invalid username/email or password.")

        # Create a new CSRF token for the session
        csrf_token = generate_csrf_token()

        # Create session in Redis
        session_data = await self.session_repo.create_session_record(user.id, csrf_token)
        logger.info(f"User '{user.username}' (ID: {user.id}) logged in successfully. Session ID: {session_data.session_id}")
        return session_data

    async def logout_user(self, session_id: uuid.UUID) -> None:
        """
        Deletes a session, effectively logging out the user.
        """
        await self.session_repo.delete_session_record(session_id)
        logger.info(f"Session {session_id} deleted (user logged out).")

    async def get_user_from_session(self, session_id: uuid.UUID) -> Optional[User]:
        """
        Retrieves the User object associated with a given session ID.
        This is typically used internally by authentication dependencies.
        """
        session_data = await self.session_repo.get_session_record(session_id)
        if not session_data:
            logger.warning(f"No session data found for session ID: {session_id}")
            return None
        
        user = await self.user_repo.get_user_by_id(session_data.user_id)
        if not user:
            logger.error(f"User ID {session_data.user_id} from session {session_id} not found in DB.")
            # This indicates a potential data inconsistency, session should probably be invalidated
            await self.session_repo.delete_session_record(session_id)
            raise UnauthorizedException(detail="Authenticated user record missing.")
            
        return user