"""Request metrics middleware for the REST API.

Logs every request with path, method, status code, and duration.
Slow requests (>5s) and server errors (>=500) are logged at higher severity.
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


async def metrics_middleware(request: Request, call_next):
    """Log request metrics: path, method, status, duration_ms.

    - status >= 500  -> logger.error("Server error", extra=...)
    - duration > 5s   -> logger.warning("Slow request", extra=...)
    - otherwise       -> logger.info("Request completed", extra=...)
    """
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    metrics = {
        "event": "request_metrics",
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "duration_ms": round(duration_ms, 2),
    }

    if response.status_code >= 500:
        logger.error("Server error", extra=metrics)
    elif duration_ms > 5000:
        logger.warning("Slow request", extra=metrics)
    else:
        logger.info("Request completed", extra=metrics)

    return response
