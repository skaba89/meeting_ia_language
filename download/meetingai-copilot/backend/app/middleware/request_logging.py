"""
Request logging middleware for MeetingAI Copilot.
Logs all HTTP requests with method, path, status, and duration.
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all HTTP requests with timing information."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()
        
        # Add request_id to request state for downstream use
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 1),
                    "client_ip": request.client.host if request.client else None,
                }
            },
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
