# Time Tracking & Role-Based Management System

A full-stack time tracking system for managing employee work hours, overtime, and user roles.

## Features

### User Roles

- **Admin**: Add/delete users, change user roles, reset passwords, view all data
- **Accountant**: View employee work logs, calculate hours, identify overtime, export reports
- **Employee**: Log start/end times, view personal work history, edit own entries

### Core Features

- JWT-based authentication
- Role-based access control
- Time logging with automatic overtime calculation
- User management (CRUD operations)
- Report generation and export (CSV/Excel)
- Audit logging

## Tech Stack

- **Backend**: FastAPI, Python, Pydantic, Boto3, JWT
- **Frontend**: React, TypeScript, TailwindCSS, Axios
- **Database**: DynamoDB (NoSQL)
- **Deployment**: Docker

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, security, dependencies
│   │   ├── db/            # DynamoDB operations
│   │   ├── models/        # Pydantic models
│   │   ├── routers/       # API endpoints
│   │   └── services/      # Business logic
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── context/       # Auth context
│   │   └── services/      # API services
│   └── package.json       # Node dependencies
└── docker-compose.yml     # Docker configuration
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS Account with DynamoDB access
- Docker (optional)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
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

5. Set up DynamoDB tables:
   - Create tables with the names specified in `.env`
   - For `users` table: Primary key `user_id` (String)
   - For `timelogs` table: Primary key `log_id` (String)
   - Optionally create GSIs:
     - `users` table: GSI on `email` (email-index)
     - `timelogs` table: GSI on `user_id` (user_id-index)

6. Run the backend:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000
```

4. Run the frontend:
```bash
npm start
```

The application will be available at `http://localhost:3000`

### Docker Setup

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

This will start both backend and frontend services.

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## DynamoDB Schema

### Users Table
- `user_id` (PK, String)
- `name` (String)
- `email` (String)
- `role` (String: admin, accountant, employee)
- `password_hash` (String)
- `created_at` (String, ISO format)

### TimeLogs Table
- `log_id` (PK, String)
- `user_id` (String)
- `start_time` (String, ISO format)
- `end_time` (String, ISO format)
- `break_duration` (Number)
- `total_hours` (Number)
- `is_overtime` (Boolean)
- `created_at` (String, ISO format)
- `updated_at` (String, ISO format, optional)

### Audit Table
- `audit_id` (PK, String)
- `action` (String)
- `user_id` (String)
- `details` (Map)
- `created_at` (String, ISO format)

## Usage

1. **Login**: Use the login page to authenticate
2. **Employee Dashboard**: Log your work hours, view your history
3. **Admin Panel**: Manage users, roles, and passwords
4. **Accountant Dashboard**: View reports, filter data, export to CSV/Excel

## Development

### Backend
- Follow FastAPI best practices
- Use type hints and Pydantic models
- Implement proper error handling

### Frontend
- Use TypeScript for type safety
- Follow React best practices
- Implement proper error handling and loading states

## License

MIT

