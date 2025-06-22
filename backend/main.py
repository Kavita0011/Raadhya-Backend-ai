# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import AsyncGenerator

from backend.config import settings
from backend.database import get_async_session_maker, init_db
from backend.middleware.request_id_middleware import RequestIDMiddleware
from backend.middleware.session_middleware import SessionMiddleware
from backend.routers import auth_router, users_router
from backend.security.auth_manager import redis_client, close_redis_connection
from backend.exceptions.custom_exceptions import (
    UserAlreadyExistsException, UserNotFoundException, IncorrectCredentialsException,
    CSRFTokenMismatchException, SessionExpiredException, UnauthorizedException, ForbiddenException
)
from fastapi.responses import JSONResponse
import logging

# Configure basic logging (for development, production should use more sophisticated setup)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
# --- Application Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles startup and shutdown events for the application.
    """
    logger.info("Application startup initiated...")

    # Initialize PostgreSQL database connection
    logger.info("Initializing PostgreSQL database...")
    await init_db()
    logger.info("PostgreSQL database initialized.")

    # Initialize Redis connection
    logger.info("Connecting to Redis...")
    await redis_client.ping() # Test Redis connection
    logger.info("Redis connection established.")

    yield # Application starts here

    # Shutdown events
    logger.info("Application shutdown initiated...")
    logger.info("Closing Redis connection...")
    await close_redis_connection()
    logger.info("Redis connection closed.")
    logger.info("Application shutdown complete.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan # Attach the lifespan context manager
)

# --- Middleware Configuration ---
# 1. Request ID Middleware (first, to ensure all logs have it)
app.add_middleware(RequestIDMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
    expose_headers=["X-CSRF-Token"] # Crucial for CSRF token delivery
)

# 3. Session Middleware (after CORS, before routes)
# This middleware will handle setting/getting the session cookie
app.add_middleware(SessionMiddleware)

# --- Global Exception Handlers ---
@app.exception_handler(UserAlreadyExistsException)
async def user_exists_exception_handler(request, exc: UserAlreadyExistsException):
    logger.warning(f"UserAlreadyExistsException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": "USER_ALREADY_EXISTS", "message": exc.detail},
    )

@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request, exc: UserNotFoundException):
    logger.warning(f"UserNotFoundException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "USER_NOT_FOUND", "message": exc.detail},
    )

@app.exception_handler(IncorrectCredentialsException)
async def incorrect_credentials_exception_handler(request, exc: IncorrectCredentialsException):
    logger.warning(f"IncorrectCredentialsException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"code": "INCORRECT_CREDENTIALS", "message": exc.detail},
    )

@app.exception_handler(SessionExpiredException)
async def session_expired_exception_handler(request, exc: SessionExpiredException):
    logger.warning(f"SessionExpiredException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"code": "SESSION_EXPIRED", "message": exc.detail},
        headers={"WWW-Authenticate": "Bearer"}, # Standard for auth errors
    )

@app.exception_handler(CSRFTokenMismatchException)
async def csrf_token_mismatch_exception_handler(request, exc: CSRFTokenMismatchException):
    logger.warning(f"CSRFTokenMismatchException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"code": "CSRF_TOKEN_MISMATCH", "message": exc.detail},
    )

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request, exc: UnauthorizedException):
    logger.warning(f"UnauthorizedException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"code": "UNAUTHORIZED", "message": exc.detail},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request, exc: ForbiddenException):
    logger.warning(f"ForbiddenException: {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"code": "FORBIDDEN", "message": exc.detail},
    )

# Generic HTTP Exception Handler (for FastAPI's HTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail} - Request ID: {request.state.request_id}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": f"HTTP_{exc.status_code}", "message": exc.detail},
    )


# --- Router Inclusion ---
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router.router, prefix="/api/users", tags=["Users"])


# --- Health Check Endpoint ---
@app.get("/health", summary="Health Check", response_model=dict)
async def health_check():
    """
    Provides a simple health check endpoint for monitoring.
    """
    try:
        # Check database connection
        async with get_async_session_maker().begin() as session:
            await session.execute("SELECT 1")
        # Check Redis connection
        await redis_client.ping()
        return {"status": "ok", "message": "Service is healthy"}
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {e}"
        )

# Example of how to run (though uvicorn in Dockerfile typically handles this)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)