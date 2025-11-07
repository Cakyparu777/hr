# Local Testing Guide with Mock Database

This guide shows you how to test the application locally using DynamoDB Local (a mock DynamoDB database).

## Quick Start

### Step 1: Start DynamoDB Local

**Using Docker (Recommended):**
```bash
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
```

**Or use the setup script:**
```bash
cd backend
source venv/bin/activate
./start_local.sh
```

### Step 2: Configure Environment

Create a `.env` file in the `backend` directory:

```env
SECRET_KEY=dev-secret-key-change-in-production
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
DYNAMODB_ENDPOINT_URL=http://localhost:8000
DYNAMODB_USERS_TABLE=time_tracking_users
DYNAMODB_TIMELOGS_TABLE=time_tracking_logs
DYNAMODB_AUDIT_TABLE=time_tracking_audit
OVERTIME_THRESHOLD_HOURS=8.0
```

### Step 3: Create Tables

```bash
cd backend
source venv/bin/activate
python setup_dynamodb.py
```

### Step 4: Create Admin User

```bash
python create_admin.py admin@admin.com password "Admin User"
```

### Step 5: Start Backend Server

```bash
uvicorn main:app --reload
```

Backend will be available at: `http://localhost:8000`

### Step 6: Start Frontend (in another terminal)

```bash
cd frontend
npm install  # First time only
npm start
```

Frontend will be available at: `http://localhost:3000`

## Testing the Application

1. **Login**: Go to `http://localhost:3000` and login with:
   - Email: `admin@admin.com`
   - Password: `password`

2. **Create Users**: As admin, go to Admin Panel and create test users

3. **Log Time**: Switch to employee account and log work hours

4. **View Reports**: As accountant/admin, view reports and export data

## API Testing

### Using Swagger UI

Visit: `http://localhost:8000/docs`

### Using curl

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "password"}'

# Get current user (use token from login)
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## DynamoDB Local Management

### View Tables
```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

### View Table Items
```bash
aws dynamodb scan --table-name time_tracking_users --endpoint-url http://localhost:8000
```

### Stop DynamoDB Local
```bash
docker stop dynamodb-local
docker rm dynamodb-local
```

### Restart DynamoDB Local
```bash
docker start dynamodb-local
```

## Troubleshooting

### Port 8000 Already in Use

If port 8000 is already in use, change the port:
```bash
docker run -d -p 8001:8000 --name dynamodb-local amazon/dynamodb-local
```

Then update `.env`:
```
DYNAMODB_ENDPOINT_URL=http://localhost:8001
```

### Tables Already Exist Error

If you get "table already exists", you can:
1. Delete the container and recreate: `docker rm -f dynamodb-local && docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local`
2. Or modify `setup_dynamodb.py` to handle existing tables gracefully

### Connection Refused

Make sure DynamoDB Local is running:
```bash
docker ps | grep dynamodb-local
```

If not running, start it:
```bash
docker start dynamodb-local
```

## Data Persistence

By default, DynamoDB Local stores data in memory. When you stop the container, all data is lost.

To persist data, mount a volume:
```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/.dynamodb:/home/dynamodblocal/data \
  --name dynamodb-local \
  amazon/dynamodb-local \
  -jar DynamoDBLocal.jar -sharedDb -dbPath /home/dynamodblocal/data
```

## Using Docker Compose (All-in-One)

Alternatively, use Docker Compose which includes everything:

```bash
docker-compose up --build
```

This starts:
- DynamoDB Local (port 8001)
- Backend (port 8000)
- Frontend (port 3000)

## Next Steps

1. Create test users with different roles
2. Log time entries
3. Test filtering and export features
4. Test role-based access control

