# Deployment Fix - EC2 Issue

## Problem

The deployment failed with:
```
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory
```

## Solution

The issue is that `Dockerfile.prod` might not exist on your EC2 instance, or Docker Compose isn't finding it correctly.

### Option 1: Verify Files Exist (Recommended)

1. **SSH into your EC2 instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. **Check if files exist**:
   ```bash
   cd /opt/time-tracking
   ls -la frontend/Dockerfile.prod
   ls -la backend/Dockerfile.prod
   ```

3. **If files don't exist, make sure you've pulled/cloned the latest code**:
   ```bash
   git pull
   # or
   git clone your-repo-url .
   ```

### Option 2: Use Regular Dockerfiles

If the `Dockerfile.prod` files aren't in your repository, you can modify `docker-compose.prod.yml` to use the regular Dockerfiles:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile  # Changed from Dockerfile.prod
    # ... rest of config

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile  # Changed from Dockerfile.prod
    # ... rest of config
```

However, the regular `Dockerfile` for frontend is for development (runs `npm start`), so you'll need to create a production version.

### Option 3: Create Production Dockerfiles on EC2

If the files don't exist, create them on EC2:

1. **Create frontend/Dockerfile.prod on EC2**:
   ```bash
   cd /opt/time-tracking/frontend
   nano Dockerfile.prod
   ```

   Paste the contents from the repository.

2. **Create backend/Dockerfile.prod on EC2** (if needed):
   ```bash
   cd /opt/time-tracking/backend
   nano Dockerfile.prod
   ```

   Paste the contents from the repository.

### Option 4: Commit and Push Files

Make sure `Dockerfile.prod` files are committed to your repository:

```bash
# On your local machine
git add frontend/Dockerfile.prod backend/Dockerfile.prod
git commit -m "Add production Dockerfiles"
git push
```

Then on EC2:
```bash
git pull
```

## Quick Fix Script

Run this on your EC2 instance to verify and fix:

```bash
cd /opt/time-tracking

# Check if files exist
if [ ! -f "frontend/Dockerfile.prod" ]; then
    echo "frontend/Dockerfile.prod not found. Creating..."
    # You'll need to create it manually or pull from repo
fi

if [ ! -f "backend/Dockerfile.prod" ]; then
    echo "backend/Dockerfile.prod not found. Creating..."
    # You'll need to create it manually or pull from repo
fi

# Verify docker-compose file
cat docker-compose.prod.yml | grep dockerfile
```

## Recommended Solution

1. **Make sure all files are committed to git**:
   - `frontend/Dockerfile.prod`
   - `backend/Dockerfile.prod`
   - `docker-compose.prod.yml`
   - `.env.prod.example`

2. **On EC2, pull the latest code**:
   ```bash
   cd /opt/time-tracking
   git pull origin main
   # or clone fresh
   git clone your-repo-url .
   ```

3. **Verify files exist**:
   ```bash
   ls -la frontend/Dockerfile.prod
   ls -la backend/Dockerfile.prod
   ```

4. **Try deploying again**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

## If Still Having Issues

Check Docker Compose version:
```bash
docker-compose --version
```

Make sure you're using Docker Compose v2 or later. If not, update:
```bash
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

Then use:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Note: `docker compose` (with space, not hyphen) is the newer version.

