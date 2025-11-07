# Setup Guide

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend` directory:

```env
SECRET_KEY=your-secret-key-change-in-production
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
DYNAMODB_USERS_TABLE=time_tracking_users
DYNAMODB_TIMELOGS_TABLE=time_tracking_logs
DYNAMODB_AUDIT_TABLE=time_tracking_audit
OVERTIME_THRESHOLD_HOURS=8.0
```

### 3. Set Up DynamoDB Tables

```bash
python setup_dynamodb.py
```

This will create the required tables:
- `time_tracking_users` (with email GSI)
- `time_tracking_logs` (with user_id GSI)
- `time_tracking_audit`

### 4. Create Initial Admin User

```bash
python create_admin.py admin@example.com password123 "Admin User"
```

### 5. Start Backend Server

```bash
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### 6. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### 7. Start Frontend

```bash
npm start
```

Frontend will be available at `http://localhost:3000`

## Using Docker

```bash
docker-compose up --build
```

This will start both services automatically.

## Accessing the Application

1. Navigate to `http://localhost:3000`
2. Login with the admin credentials you created
3. Start using the system!

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

