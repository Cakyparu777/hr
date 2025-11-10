from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    
    # DynamoDB
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    DYNAMODB_ENDPOINT_URL: str = ""  # For DynamoDB Local, use "http://localhost:8000"
    DYNAMODB_USERS_TABLE: str = "time_tracking_users"
    DYNAMODB_TIMELOGS_TABLE: str = "time_tracking_logs"
    DYNAMODB_AUDIT_TABLE: str = "time_tracking_audit"
    DYNAMODB_HOLIDAYS_TABLE: str = "time_tracking_holidays"
    
    # Time Tracking Settings
    OVERTIME_THRESHOLD_HOURS: float = 8.0  # Hours per day before overtime
    WORK_DAYS_PER_WEEK: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

