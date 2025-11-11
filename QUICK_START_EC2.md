# Quick Start - EC2 Deployment

## Prerequisites

- AWS EC2 instance (Ubuntu 20.04+)
- SSH access to EC2
- AWS credentials with DynamoDB access

## 5-Minute Setup

### 1. Launch EC2 Instance

- **AMI**: Ubuntu Server 20.04 LTS
- **Instance Type**: t2.small (recommended) or t2.micro (free tier)
- **Security Group**: 
  - Port 22 (SSH) from your IP
  - Port 80 (HTTP) from 0.0.0.0/0
  - Port 8000 (Backend API) from 0.0.0.0/0 (optional)

### 2. Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Run Setup Script

```bash
# Download setup script (or clone repo first)
curl -O https://raw.githubusercontent.com/your-repo/time-tracking/main/backend/deploy-ec2.sh
chmod +x deploy-ec2.sh
./deploy-ec2.sh

# Log out and back in for Docker group changes
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 4. Clone Repository

```bash
sudo mkdir -p /opt/time-tracking
sudo chown $USER:$USER /opt/time-tracking
cd /opt/time-tracking
git clone https://github.com/your-username/your-repo.git .
```

### 5. Configure Environment

```bash
# Copy example env file
cp .env.prod.example .env.prod

# Edit environment variables
nano .env.prod
```

Update these values:

```env
SECRET_KEY=your-generated-secret-key
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
CORS_ORIGINS=http://your-ec2-ip,http://your-domain.com
REACT_APP_API_URL=http://your-ec2-ip:8000
```

Generate SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Initialize DynamoDB

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
```

### 7. Verify Deployment Files

```bash
cd /opt/time-tracking

# Run verification script (creates missing files if needed)
./verify-deployment.sh
```

### 8. Deploy Application

```bash
cd /opt/time-tracking

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Start services
docker-compose -f docker-compose.prod.yml up -d --build

# Or if using Docker Compose v2:
# docker compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 9. Access Application

- **Frontend**: `http://your-ec2-ip`
- **Backend API**: `http://your-ec2-ip:8000`
- **API Docs**: `http://your-ec2-ip:8000/docs`

### 10. Login

- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ Change password immediately!**

## Troubleshooting

```bash
# Check containers
docker ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

## Next Steps

1. Set up SSL certificate (Let's Encrypt)
2. Configure custom domain
3. Set up auto-start on boot
4. Configure monitoring

See `EC2_DEPLOYMENT.md` for detailed instructions.

