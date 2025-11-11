from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import auth, users, timelogs, reports, holidays, leave_requests
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.exceptions import AppException

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Middleware to silently handle WebSocket connection attempts from React HMR
class WebSocketFilterMiddleware(BaseHTTPMiddleware):
    """Silently handle harmless WebSocket connection attempts from React HMR."""
    async def dispatch(self, request: Request, call_next):
        # Silently handle WebSocket upgrade requests to /ws (React HMR)
        # These are harmless and don't need to be logged
        if request.url.path == "/ws":
            from fastapi.responses import JSONResponse
            # Return 400 without logging to reduce noise
            return JSONResponse(
                status_code=400,
                content={"detail": "WebSocket endpoint not available"}
            )
        return await call_next(request)

# Initialize rate limiter (optional - only if slowapi is installed)
RATE_LIMITING_AVAILABLE = False
limiter = None
RateLimitExceeded = None
_rate_limit_exceeded_handler = None

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    logger.warning("slowapi not installed - rate limiting disabled")

app = FastAPI(
    title="Time Tracking API",
    description="Time tracking and role-based management system",
    version="1.0.0"
)

# Store settings in app state for error handlers
app.state.settings = settings

# Add rate limiter (if available)
if RATE_LIMITING_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled")
else:
    logger.warning("Rate limiting disabled - slowapi not installed")

# Add WebSocket filter middleware (before CORS)
app.add_middleware(WebSocketFilterMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(timelogs.router, prefix="/api/timelogs", tags=["Time Logs"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(holidays.router, prefix="/api/holidays", tags=["Holidays"])
app.include_router(leave_requests.router, prefix="/api/leave-requests", tags=["Leave Requests"])

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "Application starting",
        environment=settings.ENVIRONMENT,
        version="1.0.0"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutting down")

@app.get("/")
async def root():
    return {"message": "Time Tracking API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # TODO: Add DynamoDB connectivity check
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

@app.get("/ws")
async def websocket_health():
    """Handle WebSocket health checks from React HMR.
    
    This endpoint exists to prevent 403 errors in logs when React's
    Hot Module Replacement tries to connect via WebSocket.
    The frontend dev server handles actual HMR connections.
    """
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=200,
        content={"message": "WebSocket endpoint - HMR handled by frontend dev server"}
    )


