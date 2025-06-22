# backend/routers/users_router.py

from fastapi import APIRouter, Depends
from typing import Annotated
import logging

from backend.schemas import UserResponse
from backend.models import User
from backend.services.user_service import UserService
from backend.repositories.user_repository import UserRepository
from backend.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dependencies.auth_dependencies import get_current_user # Protected route dependency

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Dependencies for Services ---
async def get_user_service(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> UserService:
    """
    Dependency to provide a UserService instance.
    """
    user_repo = UserRepository(db_session)
    return UserService(user_repo)

# --- User Endpoints ---

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user's profile",
)
async def read_current_user_me(
    current_user: Annotated[User, Depends(get_current_user)], # This dependency ensures authentication and CSRF validation
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Retrieves the profile of the currently authenticated user.
    """
    logger.info(f"Retrieving profile for user: {current_user.username}")
    # The current_user object already contains the necessary data,
    # but we can use the service layer for consistency or if there's
    # additional business logic to apply before returning.
    # For now, directly returning from current_user is efficient.
    return UserResponse.model_validate(current_user)

# Add more user-specific routes here, e.g.,
# @router.put("/me", response_model=UserResponse)
# async def update_current_user_profile(...):
#    ...