# backend/exceptions/custom_exceptions.py

from fastapi import HTTPException, status

# --- Authentication and User Related Exceptions ---

class UserAlreadyExistsException(HTTPException):
    """
    Exception raised when a user tries to register with an existing username or email.
    Maps to HTTP 409 Conflict.
    """
    def __init__(self, detail: str = "Username or email already registered."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class UserNotFoundException(HTTPException):
    """
    Exception raised when a requested user is not found.
    Maps to HTTP 404 Not Found.
    """
    def __init__(self, detail: str = "User not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class IncorrectCredentialsException(HTTPException):
    """
    Exception raised for invalid login credentials (username/email or password).
    Maps to HTTP 401 Unauthorized.
    """
    def __init__(self, detail: str = "Invalid username/email or password."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"}) # Standard header for auth challenges

# --- Session and Security Related Exceptions ---

class SessionExpiredException(HTTPException):
    """
    Exception raised when an active session has expired.
    Maps to HTTP 401 Unauthorized.
    """
    def __init__(self, detail: str = "Session has expired. Please log in again."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})

class CSRFTokenMismatchException(HTTPException):
    """
    Exception raised when the CSRF token provided in the request does not match the session's token.
    Maps to HTTP 403 Forbidden.
    """
    def __init__(self, detail: str = "CSRF token validation failed. Request forbidden."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

# --- General Authorization Exceptions ---

class UnauthorizedException(HTTPException):
    """
    Generic exception for unauthenticated requests.
    Maps to HTTP 401 Unauthorized.
    """
    def __init__(self, detail: str = "Not authenticated. Please log in."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})

class ForbiddenException(HTTPException):
    """
    Exception raised when an authenticated user does not have permission to perform an action.
    Maps to HTTP 403 Forbidden.
    """
    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

# Add more specific exceptions as your application grows
# For example:
# class ResourceNotFoundException(HTTPException):
#     def __init__(self, detail: str = "Resource not found."):
#         super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

# class ConflictException(HTTPException):
#     def __init__(self, detail: str = "Conflicting resource exists."):
#         super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)