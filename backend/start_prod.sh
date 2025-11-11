#!/bin/bash
set -e

echo "=== Starting Production Backend ==="

# Initialize database tables (idempotent - safe to run multiple times)
echo "Initializing database tables..."
python init_db.py || echo "Warning: Database initialization failed, continuing anyway..."

# Create default admin user if it doesn't exist (idempotent)
echo "Creating default admin user if needed..."
python create_default_admin.py || echo "Warning: Default admin creation failed, continuing anyway..."

# Start the server
echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log

