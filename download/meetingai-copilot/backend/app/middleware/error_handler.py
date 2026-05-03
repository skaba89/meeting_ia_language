"""
Global error handler middleware for MeetingAI Copilot.
Catches all exceptions and returns structured JSON error responses.
"""
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.exceptions import MeetingAIError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that catches all exceptions and returns structured error responses."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except MeetingAIError as exc:
            logger.warning(
                f"Application error: {exc.code} - {exc.message}",
                extra={"extra_data": {"code": exc.code, "details": exc.details}},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    }
                },
            )
        except Exception as exc:
            logger.error(
                f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred. Please try again later.",
                    }
                },
            )
