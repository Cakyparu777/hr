from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os
import secrets

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens
    
    # Security Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5  # Stricter for auth endpoints
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # DynamoDB
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    DYNAMODB_ENDPOINT_URL: str = ""  # For DynamoDB Local, use "http://localhost:8000"
    DYNAMODB_USERS_TABLE: str = "time_tracking_users"
    DYNAMODB_TIMELOGS_TABLE: str = "time_tracking_logs"
    DYNAMODB_AUDIT_TABLE: str = "time_tracking_audit"
    DYNAMODB_HOLIDAYS_TABLE: str = "time_tracking_holidays"
    DYNAMODB_LEAVE_REQUESTS_TABLE: str = "time_tracking_leave_requests"
    
    # Time Tracking Settings
    OVERTIME_THRESHOLD_HOURS: float = 8.0  # Hours per day before overtime
    WORK_DAYS_PER_WEEK: int = 5
    MAX_HOURS_PER_DAY: float = 24.0  # Maximum hours that can be logged per day
    MAX_EDIT_DAYS: int = 30  # Days after which employees can't edit logs
    ALLOW_MULTIPLE_LOGS_PER_DAY: bool = True  # Allow multiple time logs per day (False = only one log per day)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()
    
    def _validate_security_settings(self):
        """Validate security-critical settings."""
        # SECRET_KEY validation
        default_secret = "your-secret-key-change-in-production"
        if not self.SECRET_KEY or self.SECRET_KEY == default_secret:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "SECRET_KEY must be set to a secure random value in production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            else:
                # Generate a random secret for development if not set
                if self.SECRET_KEY == default_secret:
                    self.SECRET_KEY = secrets.token_urlsafe(32)
                    print(f"WARNING: Using auto-generated SECRET_KEY for development. Set SECRET_KEY in .env for production.")

settings = Settings()

