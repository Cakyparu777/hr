# EC2 Deployment Troubleshooting

## Common Issues and Solutions

### Issue: "failed to read dockerfile: open Dockerfile: no such file or directory"

**Solution**: Run the verification script to create missing files:

```bash
cd /opt/time-tracking
./verify-deployment.sh
```

This script will automatically create `backend/Dockerfile.prod` and `frontend/Dockerfile.prod` if they don't exist.

### Issue: Docker Compose Version

If you get errors about docker-compose syntax, check your version:

```bash
docker-compose --version
```

If you have Docker Compose v2 (newer), use:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

(Note: `docker compose` with space, not hyphen)

### Issue: Backend Health Check Fails

The backend health check uses Python instead of curl. If it fails:

1. Check if the backend is running:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Check backend logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   ```

3. Test health endpoint manually:
   ```bash
   curl http://localhost:8000/health
   ```

### Issue: Frontend Can't Connect to Backend

1. Check if backend is running and healthy:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Verify network connectivity:
   ```bash
   docker-compose -f docker-compose.prod.yml exec frontend ping backend
   ```

3. Check nginx configuration in frontend container:
   ```bash
   docker-compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf
   ```

4. Verify `REACT_APP_API_URL` in `.env.prod`:
   ```bash
   grep REACT_APP_API_URL .env.prod
   ```

### Issue: Environment Variables Not Loading

Make sure to export environment variables before running docker-compose:

```bash
export $(cat .env.prod | grep -v '^#' | xargs)
docker-compose -f docker-compose.prod.yml up -d --build
```

Or use a `.env` file (docker-compose automatically loads `.env`):

```bash
cp .env.prod .env
docker-compose -f docker-compose.prod.yml up -d --build
```

### Issue: Port Already in Use

If port 80 or 8000 is already in use:

1. Check what's using the port:
   ```bash
   sudo netstat -tulpn | grep -E '80|8000'
   ```

2. Stop the conflicting service or change ports in `docker-compose.prod.yml`

### Issue: Permission Denied

If you get permission errors:

1. Make sure you're in the docker group:
   ```bash
   groups
   ```

2. If not, add yourself and log out/in:
   ```bash
   sudo usermod -aG docker $USER
   exit
   # Log back in
   ```

3. Or use sudo (not recommended):
   ```bash
   sudo docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Issue: DynamoDB Connection Errors

1. Verify AWS credentials in `.env.prod`:
   ```bash
   grep AWS .env.prod
   ```

2. Test AWS credentials:
   ```bash
   aws dynamodb list-tables --region us-east-1
   ```

3. Check if tables exist:
   ```bash
   aws dynamodb describe-table --table-name time_tracking_users --region us-east-1
   ```

4. Initialize tables if needed:
   ```bash
   cd backend
   python3 init_db.py
   ```

### Issue: Build Fails with npm install

If frontend build fails during `npm install`:

1. Check node_modules in build context (should be excluded):
   ```bash
   cat frontend/.dockerignore
   ```

2. Clear Docker cache and rebuild:
   ```bash
   docker-compose -f docker-compose.prod.yml build --no-cache frontend
   ```

### Issue: Container Keeps Restarting

1. Check container logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   docker-compose -f docker-compose.prod.yml logs frontend
   ```

2. Check container status:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

3. Check if health checks are passing:
   ```bash
   docker inspect <container-id> | grep -A 10 Health
   ```

### Issue: Files Not Found in Container

If files are missing in the container:

1. Check `.dockerignore` files:
   ```bash
   cat backend/.dockerignore
   cat frontend/.dockerignore
   ```

2. Verify files exist in build context:
   ```bash
   ls -la backend/
   ls -la frontend/
   ```

3. Rebuild without cache:
   ```bash
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

## Getting Help

1. Check logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

2. Check container status:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

3. Check Docker system:
   ```bash
   docker system df
   docker system prune  # Clean up if needed
   ```

4. Verify all files exist:
   ```bash
   ./verify-deployment.sh
   ```

## Quick Diagnostic Commands

```bash
# Check if all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs for all services
docker-compose -f docker-compose.prod.yml logs

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost

# Check Docker network
docker network ls
docker network inspect hr_app-network

# Check container resources
docker stats

# Check disk space
df -h
docker system df
```

## Common Fixes

### Rebuild Everything

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Reset Everything

```bash
docker-compose -f docker-compose.prod.yml down -v
docker system prune -a
./verify-deployment.sh
docker-compose -f docker-compose.prod.yml up -d --build
```

### Check Configuration

```bash
# Verify docker-compose file syntax
docker-compose -f docker-compose.prod.yml config

# Verify environment variables
cat .env.prod

# Verify files exist
./verify-deployment.sh
```

