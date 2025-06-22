# backend/dependencies/auth_dependencies.py

from fastapi import Request, Depends, HTTPException, status
from typing import Annotated
import uuid
import logging

from backend.schemas import SessionData
from backend.exceptions.custom_exceptions import (
    SessionExpiredException, UnauthorizedException, CSRFTokenMismatchException, UserNotFoundException
)
from backend.security.csrf import validate_csrf_token
from backend.repositories.user_repository import UserRepository
from backend.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User # Import User model for type hinting

logger = logging.getLogger(__name__)

async def get_current_session_data(request: Request) -> SessionData:
    """
    Dependency that retrieves the current session data from request.state.
    Raises UnauthorizedException if no valid session data is found.
    """
    session_data: SessionData = request.state.session_data
    if not session_data:
        logger.warning(f"Unauthorized: No valid session data found for request ID: {request.state.request_id}")
        raise UnauthorizedException(detail="Not authenticated. Please log in.")
    
    # Optionally, you might add more granular checks here if get_session in auth_manager
    # didn't already raise SessionExpiredException.
    # If get_session raises, main.py's exception handler will catch it.
    
    return session_data

async def get_current_user_id_and_validate_csrf(
    request: Request,
    session_data: Annotated[SessionData, Depends(get_current_session_data)]
) -> uuid.UUID:
    """
    Dependency that validates the CSRF token and returns the current user's ID.
    Raises CSRFTokenMismatchException if the token is invalid.
    """
    # CSRF token is expected in a custom header for state-changing methods (POST, PUT, PATCH, DELETE)
    # For GET/HEAD/OPTIONS, CSRF token validation can be skipped or made optional.
    # We enforce it for all authenticated requests for simplicity in this example,
    # but you might want to scope this based on HTTP method in production.
    if request.method not in ["GET", "HEAD", "OPTIONS"]:
        received_csrf_token = request.headers.get("X-CSRF-Token")
        
        if not received_csrf_token:
            logger.warning(f"CSRF Token Missing for {request.method} {request.url} - Request ID: {request.state.request_id}")
            raise CSRFTokenMismatchException(detail="CSRF token is missing.")
            
        if not validate_csrf_token(session_data.csrf_token, received_csrf_token):
            logger.warning(f"CSRF Token Mismatch for user {session_data.user_id} on {request.method} {request.url} - Request ID: {request.state.request_id}")
            raise CSRFTokenMismatchException(detail="CSRF token validation failed.")
    
    logger.debug(f"CSRF token validated for user {session_data.user_id} - Request ID: {request.state.request_id}")
    return session_data.user_id

async def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id_and_validate_csrf)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)]
) -> User:
    """
    Dependency that fetches the full User object for the current authenticated user.
    """
    user_repo = UserRepository(db_session)
    user = await user_repo.get_user_by_id(user_id)
    
    if not user:
        logger.error(f"User with ID {user_id} not found despite valid session - Request ID: {request.state.request_id}")
        # This case should ideally not happen if session data is consistent with DB.
        # It might indicate a data integrity issue or race condition.
        raise UnauthorizedException(detail="Authenticated user not found.")
        
    logger.debug(f"Authenticated user {user.username} retrieved - Request ID: {request.state.request_id}")
    return user

# Optional: Dependency for checking admin roles (example)
async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to ensure the current user has admin privileges.
    Example: Add a 'is_admin' field to User model for this to work.
    """
    # Assuming 'is_admin' field in User model for demonstration
    # if not current_user.is_admin:
    #     raise ForbiddenException(detail="Insufficient permissions. Admin access required.")
    # logger.info(f"Admin user {current_user.username} granted access - Request ID: {request.state.request_id}")
    # return current_user
    raise NotImplementedError("Admin role check not implemented in User model yet.") # Placeholder