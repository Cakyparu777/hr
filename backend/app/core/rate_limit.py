"""
Rate limiting utilities.
"""
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

def get_rate_limiter(request: Request) -> Limiter:
    """Get rate limiter from app state."""
    return request.app.state.limiter


async def check_rate_limit(request: Request, limit_per_minute: int):
    """
    Check rate limit for a request.
    
    Args:
        request: FastAPI request
        limit_per_minute: Rate limit per minute
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    limiter = get_rate_limiter(request)
    key = get_remote_address(request)
    
    # Check rate limit
    limiter.hit(f"{limit_per_minute}/minute", key)
    
    # Note: slowapi handles rate limit checking automatically via decorators
    # This is a manual check for endpoints that can't use decorators easily

