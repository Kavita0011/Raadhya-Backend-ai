# backend/routers/auth_router.py

from fastapi import APIRouter, Depends, Response, Request, status
from typing import Annotated
import logging

from backend.schemas import UserCreate, LoginRequest, UserResponse, MessageResponse
from backend.services.auth_service import AuthService
from backend.services.user_service import UserService # Might be needed for user-related details
from backend.repositories.user_repository import UserRepository
from backend.repositories.session_repository import SessionRepository
from backend.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dependencies.auth_dependencies import get_current_session_data # To check existing session

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Dependencies for Services ---
async def get_auth_service(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> AuthService:
    """
    Dependency to provide an AuthService instance.
    """
    user_repo = UserRepository(db_session)
    session_repo = SessionRepository() # SessionRepository doesn't need db_session
    return AuthService(user_repo, session_repo)

# --- Authentication Endpoints ---

@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Registers a new user with a unique username and email.
    """
    logger.info(f"Registering new user: {user_data.username}")
    await auth_service.register_user(user_data)
    return {"message": "User registered successfully!"}

@router.post(
    "/login",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in a user and create a session"
)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Logs in a user, establishes a session, and returns a CSRF token.
    The session ID is set as an HttpOnly cookie.
    The CSRF token is returned in the 'X-CSRF-Token' response header.
    """
    logger.info(f"Login attempt for: {login_data.username_or_email} - Request ID: {request.state.request_id}")
    
    # Perform login and create session
    session_data = await auth_service.login_user(login_data)
    
    # SessionMiddleware will pick up request.state.session_data and set the cookie
    request.state.session_data = session_data 
    
    # Return CSRF token in header for SPA
    response.headers["X-CSRF-Token"] = session_data.csrf_token
    
    logger.info(f"User {session_data.user_id} logged in, session {session_data.session_id} created. - Request ID: {request.state.request_id}")
    return {"message": "Login successful!"}

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out the current user"
)
async def logout(
    request: Request,
    response: Response, # Need access to response to clear cookie
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session_data: Annotated[SessionData, Depends(get_current_session_data)] # Ensure user is logged in
):
    """
    Logs out the current user by invalidating their session.
    Requires a valid session cookie and CSRF token.
    """
    logger.info(f"Logout attempt for session ID: {session_data.session_id} - Request ID: {request.state.request_id}")
    
    await auth_service.logout_user(session_data.session_id)
    
    # Instruct SessionMiddleware to clear the cookie
    request.state.session_deleted = True 
    
    logger.info(f"Session {session_data.session_id} successfully invalidated. - Request ID: {request.state.request_id}")
    return {"message": "Logged out successfully!"}