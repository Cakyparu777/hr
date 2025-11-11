#!/bin/bash
set -e

echo "=== Starting Backend ==="

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Wait for DynamoDB to be ready
echo "Waiting for DynamoDB..."
sleep 10

# Initialize database tables
echo "Initializing database tables..."
python init_db.py

# Create default admin user
echo "Creating default admin user..."
python create_default_admin.py

# Recalculate overtime for all existing logs (one-time migration, safe to run multiple times)
echo "Recalculating overtime for existing logs..."
python recalculate_overtime.py || echo "Warning: Overtime recalculation failed, continuing anyway..."

# Start the server
echo "Starting uvicorn server..."
# Use --no-access-log to suppress access logs (which include WebSocket connection attempts)
# Application logs (warnings, errors) will still be shown
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --no-access-log

