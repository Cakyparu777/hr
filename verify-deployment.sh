#!/bin/bash
# Verify deployment files exist before deploying

set -e

echo "Verifying deployment files..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check backend Dockerfile.prod
if [ ! -f "backend/Dockerfile.prod" ]; then
    echo "Error: backend/Dockerfile.prod not found"
    echo "Creating backend/Dockerfile.prod..."
    cat > backend/Dockerfile.prod << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start_prod.sh

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check using Python (more reliable than curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Use startup script for production
CMD ["./start_prod.sh"]
EOF
    echo "✓ Created backend/Dockerfile.prod"
else
    echo "✓ backend/Dockerfile.prod exists"
fi

# Check frontend Dockerfile.prod
if [ ! -f "frontend/Dockerfile.prod" ]; then
    echo "Error: frontend/Dockerfile.prod not found"
    echo "Creating frontend/Dockerfile.prod..."
    cat > frontend/Dockerfile.prod << 'EOF'
# Multi-stage build for production
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build arguments
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8000/api; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
    echo "✓ Created frontend/Dockerfile.prod"
else
    echo "✓ frontend/Dockerfile.prod exists"
fi

# Check .env.prod
if [ ! -f ".env.prod" ]; then
    if [ -f ".env.prod.example" ]; then
        echo "Warning: .env.prod not found, copying from .env.prod.example"
        cp .env.prod.example .env.prod
        echo "⚠ Please edit .env.prod with your actual values before deploying"
    else
        echo "Warning: .env.prod not found and .env.prod.example doesn't exist"
        echo "You'll need to create .env.prod manually"
    fi
else
    echo "✓ .env.prod exists"
fi

# Check docker-compose.prod.yml
if [ -f "docker-compose.prod.yml" ]; then
    echo "✓ docker-compose.prod.yml exists"
else
    echo "Error: docker-compose.prod.yml not found"
    exit 1
fi

echo ""
echo "All deployment files verified!"
echo ""
echo "Next steps:"
echo "1. Edit .env.prod with your actual values"
echo "2. Run: docker-compose -f docker-compose.prod.yml up -d --build"

