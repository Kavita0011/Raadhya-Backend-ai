# backend/middleware/request_id_middleware.py

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate a unique request ID for each incoming request
    and attach it to the request state and response headers.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("RequestIDMiddleware initialized.")

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log the incoming request with its ID
        logger.info(f"Incoming request: {request.method} {request.url} - Request ID: {request_id}")

        response = await call_next(request)

        # Add the request ID to the response headers
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Outgoing response: {response.status_code} - Request ID: {request_id}")

        return response