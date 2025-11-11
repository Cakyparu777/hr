#!/bin/bash
# Don't use set -e here, we want to continue even if init scripts fail

echo "=== Starting Production Backend ==="

# Initialize database tables (idempotent - safe to run multiple times)
echo "Initializing database tables..."
python init_db.py || {
    echo "Warning: Database initialization failed, continuing anyway..."
    echo "This is normal if tables already exist or if there's a temporary connection issue."
}

# Wait a moment for tables to be ready (if they were just created)
sleep 2

# Create default admin user if it doesn't exist (idempotent)
echo "Creating default admin user if needed..."
python create_default_admin.py || {
    echo "Warning: Default admin creation failed, continuing anyway..."
    echo "This is normal if admin user already exists or if there's a temporary connection issue."
}

# Start the server
echo "Starting uvicorn server..."
echo "=== Backend is ready! ==="
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log

