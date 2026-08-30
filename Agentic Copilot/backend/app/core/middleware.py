import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time_ms = (time.time() - start_time) * 1000
        formatted_process_time = f"{process_time_ms:.2f}ms"
        
        logger.info(
            f"METHOD={request.method} PATH={request.url.path} "
            f"STATUS={response.status_code} LATENCY={formatted_process_time}"
        )
        
        return response
