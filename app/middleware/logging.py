from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("examready")

class PerformanceLogger(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process Request
        response = await call_next(request)
        
        # Calculate Duration
        process_time = (time.time() - start_time) * 1000 # ms
        
        # Log details
        logger.info(
            f"⚡ {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.2f}ms"
        )
        
        return response