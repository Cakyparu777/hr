#!/bin/bash

# Script to start local development environment with DynamoDB Local

echo "🚀 Starting Local Development Environment..."

# Check if DynamoDB Local container is running
if ! docker ps | grep -q dynamodb-local; then
    echo "📦 Starting DynamoDB Local..."
    docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
    echo "✅ DynamoDB Local started on port 8000"
    sleep 2
else
    echo "✅ DynamoDB Local is already running"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
SECRET_KEY=dev-secret-key-change-in-production
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
DYNAMODB_ENDPOINT_URL=http://localhost:8000
DYNAMODB_USERS_TABLE=time_tracking_users
DYNAMODB_TIMELOGS_TABLE=time_tracking_logs
DYNAMODB_AUDIT_TABLE=time_tracking_audit
OVERTIME_THRESHOLD_HOURS=8.0
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Please run: source venv/bin/activate"
    exit 1
fi

# Create tables
echo "📊 Creating DynamoDB tables..."
python setup_dynamodb.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create an admin user: python create_admin.py admin@admin.com password \"Admin User\""
echo "2. Start the backend: uvicorn main:app --reload"
echo "3. In another terminal, start the frontend: cd ../frontend && npm start"
echo ""

