# backend/security/csrf.py

import secrets
import logging

logger = logging.getLogger(__name__)

def generate_csrf_token() -> str:
    """
    Generates a secure, random CSRF token.
    Uses Python's `secrets` module for cryptographic strength.
    """
    token = secrets.token_urlsafe(32) # Generate a 32-byte (256-bit) URL-safe text string
    logger.debug(f"Generated new CSRF token: {token[:5]}...") # Log beginning for debug, not full token
    return token

def validate_csrf_token(expected_token: str, received_token: str) -> bool:
    """
    Validates a received CSRF token against an expected token in a time-safe manner.
    This prevents timing attacks where an attacker could infer character matches.
    """
    if not expected_token or not received_token:
        logger.warning("CSRF validation failed: Missing expected or received token.")
        return False
    
    # Use secrets.compare_digest for constant-time comparison to prevent timing attacks
    is_valid = secrets.compare_digest(expected_token, received_token)
    
    if not is_valid:
        logger.warning("CSRF validation failed: Token mismatch.")
    else:
        logger.debug("CSRF token validated successfully.")
        
    return is_valid