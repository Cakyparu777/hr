#!/bin/bash
# Quick script to check if all services are running and accessible

echo "=== Checking Services ==="
echo ""

# Check Docker containers
echo "1. Docker Containers:"
docker-compose ps
echo ""

# Check Backend Health
echo "2. Backend Health:"
curl -s http://localhost:8000/health || echo "❌ Backend not accessible"
echo ""
echo ""

# Check DynamoDB
echo "3. DynamoDB:"
curl -s http://localhost:8001 || echo "❌ DynamoDB not accessible"
echo ""
echo ""

# Check Frontend
echo "4. Frontend:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000 || echo "❌ Frontend not accessible"
echo ""

echo "=== Summary ==="
echo "If all services show ✅ or HTTP 200, everything is running correctly."
echo "If you see ❌, check the logs with: docker-compose logs [service-name]"

