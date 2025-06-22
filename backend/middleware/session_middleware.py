# backend/middleware/session_middleware.py

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import uuid

from backend.config import settings
from backend.security.auth_manager import get_session, create_session, delete_session
from backend.schemas import SessionData

logger = logging.getLogger(__name__)

class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage session cookies and load session data from Redis.
    Attaches `request.state.session_data` if a valid session exists.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("SessionMiddleware initialized.")

    async def dispatch(self, request: Request, call_next):
        session_id_str = request.cookies.get(settings.SESSION_COOKIE_NAME)
        session_data: Optional[SessionData] = None

        if session_id_str:
            try:
                session_id = uuid.UUID(session_id_str)
                session_data = await get_session(session_id)
            except (ValueError, Exception) as e:
                logger.warning(f"Invalid session ID '{session_id_str}' or error retrieving session: {e} - Request ID: {request.state.request_id}")
                # Treat as no session if invalid ID or retrieval error
                session_id_str = None
                session_data = None
        
        request.state.session_data = session_data # Make session data available to routes/dependencies

        response = await call_next(request)

        # Handle setting/clearing session cookie in the response
        # If session_data was set/updated during the request (e.g., login, session refresh)
        # or if it needs to be cleared (e.g., logout, session expiry detected by get_session)
        
        # Check if the session was explicitly marked for deletion (e.g., by logout)
        if getattr(request.state, "session_deleted", False):
            response.delete_cookie(
                key=settings.SESSION_COOKIE_NAME,
                domain=settings.SESSION_COOKIE_DOMAIN,
                path="/"
            )
            logger.info(f"Session cookie '{settings.SESSION_COOKIE_NAME}' deleted - Request ID: {request.state.request_id}")
        elif request.state.session_data and request.state.session_data.session_id:
            # If session data exists and is valid, ensure cookie is set/updated
            # Redis `setex` extends TTL, so we just need to ensure the cookie is present.
            # We also need to set the cookie if a new session was created during the request (e.g., login)
            response.set_cookie(
                key=settings.SESSION_COOKIE_NAME,
                value=str(request.state.session_data.session_id),
                max_age=settings.SESSION_ABSOLUTE_TIMEOUT, # Cookie's max_age should align with absolute session timeout
                expires=request.state.session_data.expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT"), # Format for Expires header
                path="/",
                domain=settings.SESSION_COOKIE_DOMAIN,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )
            logger.debug(f"Session cookie '{settings.SESSION_COOKIE_NAME}' set/refreshed - Request ID: {request.state.request_id}")
        # If session_id_str was present but no session_data was retrieved, it means an invalid/expired cookie
        # We should ensure the cookie is cleared in the browser
        elif session_id_str and not session_data:
             response.delete_cookie(
                key=settings.SESSION_COOKIE_NAME,
                domain=settings.SESSION_COOKIE_DOMAIN,
                path="/"
            )
             logger.warning(f"Invalid/Expired session cookie '{settings.SESSION_COOKIE_NAME}' detected and deleted - Request ID: {request.state.request_id}")

        return response