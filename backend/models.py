# backend/models.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from backend.database import Base # Import Base from your database.py

# Base = declarative_base() # Moved to database.py to avoid circular imports and centralize

class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    Stores user authentication and profile information.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# Note on Sessions:
# The session state itself (session ID, CSRF token, expiry)
# is primarily managed in Redis for performance and scalability.
# Therefore, we do NOT define a 'Session' table in PostgreSQL models.
# The 'user_id' within the Redis session data directly links to the 'users' table.
# This keeps the PostgreSQL schema focused on core application data,
# and Redis handles the transient, high-velocity session state.