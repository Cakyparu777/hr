from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, timelogs, reports, holidays
from app.core.config import settings

app = FastAPI(
    title="Time Tracking API",
    description="Time tracking and role-based management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(timelogs.router, prefix="/api/timelogs", tags=["Time Logs"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(holidays.router, prefix="/api/holidays", tags=["Holidays"])

@app.get("/")
async def root():
    return {"message": "Time Tracking API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

