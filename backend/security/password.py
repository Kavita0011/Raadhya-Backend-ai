# backend/security/password.py

from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Create a CryptContext instance for password hashing
# schemes: List of hashing algorithms to use. bcrypt is recommended.
# deprecated: Schemes that are no longer recommended.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    """
    try:
        hashed_pw = pwd_context.hash(password)
        logger.debug("Password hashed successfully.")
        return hashed_pw
    except Exception as e:
        logger.error(f"Error hashing password: {e}", exc_info=True)
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        # This can happen if hashed_password is malformed or wrong format
        return False # Treat as invalid if verification itself fails