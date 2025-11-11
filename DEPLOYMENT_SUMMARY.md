# Deployment Summary

## EC2 Deployment - Quick Reference

### Files Created

1. **`docker-compose.prod.yml`** - Production Docker Compose configuration
2. **`frontend/Dockerfile.prod`** - Production frontend Dockerfile (multi-stage build with nginx)
3. **`backend/deploy-ec2.sh`** - EC2 setup script (installs Docker, Docker Compose, etc.)
4. **`backend/start-ec2.sh`** - Quick start script for EC2
5. **`.env.prod.example`** - Example environment variables file
6. **`EC2_DEPLOYMENT.md`** - Detailed deployment guide

### Quick Deployment Steps

1. **Launch EC2 Instance**
   - Ubuntu 20.04+ LTS
   - t2.small or larger
   - Security group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS optional)

2. **SSH into EC2**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Run Setup Script**
   ```bash
   ./backend/deploy-ec2.sh
   ```

4. **Clone Repository**
   ```bash
   sudo mkdir -p /opt/time-tracking
   sudo chown $USER:$USER /opt/time-tracking
   cd /opt/time-tracking
   git clone your-repo-url .
   ```

5. **Configure Environment**
   ```bash
   cp .env.prod.example .env.prod
   nano .env.prod
   # Update SECRET_KEY, AWS credentials, CORS_ORIGINS, REACT_APP_API_URL
   ```

6. **Deploy**
   ```bash
   export $(cat .env.prod | xargs)
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

7. **Access Application**
   - Frontend: `http://your-ec2-ip`
   - Backend API: `http://your-ec2-ip:8000`
   - API Docs: `http://your-ec2-ip:8000/docs`

### Default Admin Credentials

- Email: `admin@example.com`
- Password: `Admin123!`

**⚠️ Change this immediately after first login!**

### Environment Variables

Required variables in `.env.prod`:

- `SECRET_KEY` - JWT secret (generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `AWS_REGION` - AWS region (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `CORS_ORIGINS` - Allowed origins (comma-separated)
- `REACT_APP_API_URL` - Backend URL for frontend

### Troubleshooting

```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Next Steps

1. Set up SSL certificate (Let's Encrypt) for HTTPS
2. Configure custom domain
3. Set up monitoring and alerts
4. Configure automated backups
5. Set up auto-start on boot (systemd service)

See `EC2_DEPLOYMENT.md` for detailed instructions.

