# EC2 Deployment Guide

Simple guide to deploy the Time Tracking application on AWS EC2.

## Prerequisites

- AWS EC2 instance (Ubuntu 20.04 or later recommended)
- SSH access to your EC2 instance
- AWS credentials with DynamoDB access
- Domain name (optional, for custom domain)

## Quick Start

### Step 1: Launch EC2 Instance

1. Go to AWS EC2 Console
2. Launch a new instance:
   - **AMI**: Ubuntu Server 20.04 LTS or later
   - **Instance Type**: t2.micro (free tier) or t2.small (recommended)
   - **Storage**: 20 GB minimum
   - **Security Group**: 
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere (0.0.0.0/0)
     - Allow HTTPS (port 443) from anywhere (optional, for SSL)
     - Allow backend API (port 8000) from anywhere or just port 80
3. Create or select a key pair for SSH access
4. Launch instance

### Step 2: Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 3: Run Setup Script

```bash
# Download and run setup script
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

Or manually:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect

# Install Git
sudo apt-get install -y git
```

### Step 4: Clone Repository

```bash
# Create app directory
sudo mkdir -p /opt/time-tracking
sudo chown $USER:$USER /opt/time-tracking
cd /opt/time-tracking

# Clone your repository
git clone https://github.com/your-username/your-repo.git .

# Or upload files using SCP from your local machine:
# scp -i your-key.pem -r /path/to/project ubuntu@your-ec2-ip:/opt/time-tracking
```

### Step 5: Configure Environment Variables

```bash
cd /opt/time-tracking

# Copy example environment file
cp .env.prod.example .env.prod

# Edit environment variables
nano .env.prod
```

Update the following:

```env
# Generate a secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# AWS credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# CORS - use your EC2 public IP or domain
CORS_ORIGINS=http://your-ec2-public-ip,http://your-domain.com

# Frontend API URL - backend will be accessible at EC2 IP:8000
REACT_APP_API_URL=http://your-ec2-public-ip:8000
```

### Step 6: Set Up DynamoDB

Make sure your DynamoDB tables exist. The application will create them automatically on first run, or you can create them manually:

```bash
# From your local machine or EC2 instance with AWS CLI configured
cd backend
python3 init_db.py
```

### Step 7: Verify Deployment Files

```bash
cd /opt/time-tracking

# Run verification script to ensure all files exist
./verify-deployment.sh
```

This script will:
- Check if `backend/Dockerfile.prod` exists (create if missing)
- Check if `frontend/Dockerfile.prod` exists (create if missing)
- Check if `.env.prod` exists (create from example if missing)
- Verify `docker-compose.prod.yml` exists

### Step 8: Build and Start Application

```bash
cd /opt/time-tracking

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Build and start with docker-compose
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

**Note**: If you're using Docker Compose v2 (newer version), use:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

(Note: `docker compose` with space, not hyphen)

### Step 9: Verify Deployment

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Frontend**:
   Open in browser: `http://your-ec2-public-ip`

3. **API Documentation**:
   Open in browser: `http://your-ec2-public-ip:8000/docs`

### Step 10: Set Up Auto-Start (Optional)

Create a systemd service to automatically start the application on boot:

```bash
sudo nano /etc/systemd/system/time-tracking.service
```

Add:

```ini
[Unit]
Description=Time Tracking Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/time-tracking
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable time-tracking.service
sudo systemctl start time-tracking.service
```

## Configuration

### Security Group Rules

Ensure your EC2 security group allows:

- **Port 22**: SSH (from your IP only)
- **Port 80**: HTTP (from 0.0.0.0/0 for web access)
- **Port 443**: HTTPS (optional, for SSL)
- **Port 8000**: Backend API (optional, if accessing API directly)

### Environment Variables

Key environment variables in `.env.prod`:

- `SECRET_KEY`: JWT secret key (generate a strong random string)
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `REACT_APP_API_URL`: Backend URL for frontend

### DynamoDB Setup

The application uses DynamoDB for data storage. Make sure:

1. DynamoDB tables are created (automatic on first run)
2. IAM user/role has DynamoDB permissions
3. Tables are in the same region as your EC2 instance

## Troubleshooting

### Application Not Starting

```bash
# Check Docker containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Cannot Access Application

1. Check security group rules
2. Check if containers are running: `docker ps`
3. Check if ports are listening: `sudo netstat -tulpn | grep -E '80|8000'`
4. Check firewall: `sudo ufw status`

### Database Connection Issues

1. Verify AWS credentials are correct
2. Check DynamoDB table permissions
3. Verify AWS region matches your DynamoDB tables
4. Check CloudWatch logs for errors

### Frontend Cannot Connect to Backend

1. Verify `REACT_APP_API_URL` in `.env.prod` is correct
2. Check CORS settings in backend
3. Verify backend is accessible: `curl http://localhost:8000/health`
4. Check nginx configuration in frontend container

## Maintenance

### Update Application

```bash
cd /opt/time-tracking

# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup

Backup DynamoDB tables regularly using AWS Backup or manual exports.

### Logs

View logs:

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Stop Application

```bash
cd /opt/time-tracking
docker-compose -f docker-compose.prod.yml down
```

### Restart Application

```bash
cd /opt/time-tracking
docker-compose -f docker-compose.prod.yml restart
```

## Default Admin Credentials

After first deployment, use these credentials to log in:

- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ IMPORTANT**: Change this password immediately after first login!

## Cost Estimation

For a small deployment (50 users):

- **EC2 t2.small**: ~$15/month
- **DynamoDB**: ~$5-10/month (depending on usage)
- **Data Transfer**: ~$1-5/month
- **Total**: ~$20-30/month

## Next Steps

1. Set up SSL certificate (Let's Encrypt) for HTTPS
2. Configure custom domain
3. Set up monitoring and alerts
4. Configure automated backups
5. Set up CI/CD for deployments

## Support

For issues or questions, check the logs and troubleshooting section above.

