#!/bin/bash
# Quick start script for EC2 deployment
# Run this after setting up the EC2 instance

set -e

cd /opt/time-tracking || {
    echo "Error: /opt/time-tracking directory not found"
    echo "Please clone the repository first"
    exit 1
}

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
else
    echo "Warning: .env.prod not found. Using defaults."
fi

# Start services
echo "Starting Time Tracking application..."
docker-compose -f docker-compose.prod.yml up -d --build

echo "Application started!"
echo "Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "Check status: docker-compose -f docker-compose.prod.yml ps"
echo "View logs: docker-compose -f docker-compose.prod.yml logs -f"

