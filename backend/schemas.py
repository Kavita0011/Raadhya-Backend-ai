# backend/schemas.py

import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# --- Generic Response Schemas ---
class MessageResponse(BaseModel):
    """
    Generic response model for simple messages.
    """
    message: str

class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    """
    code: str = Field(..., description="A unique code for the error type")
    message: str = Field(..., description="A human-readable error message")
    details: Optional[dict] = Field(None, description="Optional additional details about the error")

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64, description="Strong password required")

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Allow Pydantic to read ORM models directly

class UserInDB(UserResponse):
    """
    Internal model representing a user from the database, including the hashed password.
    Used by services/repositories, not exposed directly in API responses.
    """
    hashed_password: str

# --- Authentication Schemas ---
class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email for login")
    password: str = Field(..., description="Password for login")

# --- Session Schemas ---
class SessionData(BaseModel):
    """
    Data stored in Redis for an active session.
    """
    session_id: uuid.UUID
    user_id: uuid.UUID
    csrf_token: str # This token will be sent to the client and validated
    created_at: datetime # When the session was created
    expires_at: datetime # Absolute expiration time of the session
    last_activity_at: datetime # Last time the session was used (for idle timeout)

    class Config:
        json_encoders = {
            uuid.UUID: lambda u: str(u), # Encode UUIDs to string when serializing to JSON/Redis
            datetime: lambda dt: dt.isoformat() # Encode datetime to ISO 8601 string
        }
        json_deserializers = {
            uuid.UUID: lambda s: uuid.UUID(s),
            datetime: lambda s: datetime.fromisoformat(s)
        }