# AWS Deployment Cost Estimate
## Time Tracking Application - 50 Users

## Overview
This document provides cost estimates for deploying the time tracking application on AWS with approximately 50 active users.

## Architecture Options

### Option 1: AWS App Runner + S3 + CloudFront ⭐ (BEST FOR CONTAINERS - Recommended)
**Best for**: Containerized apps, zero infrastructure management, auto-scaling, simplest setup

### Option 2: AWS Lightsail Containers + S3 + CloudFront (Simple & Cheap)
**Best for**: Small apps, fixed pricing, predictable costs, easy setup

### Option 3: ECS Fargate + S3 + CloudFront (Flexible)
**Best for**: More control, custom configurations, advanced features

### Option 4: EC2 + S3 + CloudFront (Traditional)
**Best for**: Full control, predictable costs, single instance

### Option 5: Serverless (Lambda + API Gateway + S3 + CloudFront)
**Best for**: Pay-per-use, auto-scaling, requires code refactoring

---

## Option 1: AWS App Runner Deployment ⭐ (BEST FOR CONTAINERS)

### What is App Runner?
AWS App Runner is a fully managed service specifically designed for containerized applications. It automatically:
- Builds and deploys from container images or source code
- Handles load balancing and auto-scaling
- Provides HTTPS endpoints
- Manages SSL certificates
- Scales to zero when idle (optional)

### Services Required:
1. **AWS App Runner** - Backend container hosting (includes load balancer, SSL, auto-scaling)
2. **DynamoDB** - Database
3. **S3** - Frontend static hosting
4. **CloudFront** - CDN for frontend
5. **ECR** - Container registry (for storing Docker images)

### Monthly Cost Breakdown:

#### 1. AWS App Runner (Backend)
- **Compute**: $0.007/vCPU-hour + $0.0008/GB-hour
- **Instance**: 1 vCPU, 2 GB RAM (minimum for FastAPI)
- **Always-on**: (1 × $0.007 × 730) + (2 × $0.0008 × 730) = $5.11 + $1.17 = **$6.28/month**
- **Auto-scaling**: Scales down to 1 instance during low traffic
- **Build time**: First 1000 build minutes free, then $0.005/minute

**Note**: App Runner can scale to zero (pause service) to save costs, but requires warm-up time.

#### 2. DynamoDB
- Same as other options: **~$0.70/month**

#### 3. S3 + CloudFront
- Same as other options: **~$0.90/month**

#### 4. ECR (Container Registry)
- **Storage**: ~500 MB = $0.10/month
- **Data transfer**: Minimal (pulls during deployment) = ~$0.01/month
- **Total**: **~$0.11/month**

### Total Monthly Cost:

**Always-on**:
- App Runner: $6.28/month
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- ECR: $0.11/month
- **Total: ~$7.99/month**

**With scale-to-zero** (pauses during inactivity):
- App Runner: ~$3-5/month (depending on usage)
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- ECR: $0.11/month
- **Total: ~$4.71-6.71/month**

### Advantages:
✅ **Simplest setup** - Just push container image, App Runner handles everything
✅ **Auto-scaling** - Automatically scales based on traffic
✅ **Built-in load balancer** - No ALB needed
✅ **HTTPS included** - SSL certificate management included
✅ **Zero infrastructure management** - No servers, clusters, or configs to manage
✅ **Cost-effective** - Cheaper than ECS Fargate for small apps

### Disadvantages:
⚠️ **Less control** - Can't customize infrastructure as much
⚠️ **Regional availability** - Available in fewer regions than ECS
⚠️ **Cold starts** - If scaled to zero, first request has warm-up time

---

## Option 2: AWS Lightsail Containers (Simple & Cheap)

### What is Lightsail Containers?
AWS Lightsail Containers is a simplified container service with fixed pricing. Perfect for small applications with predictable traffic.

### Services Required:
1. **Lightsail Container Service** - Backend container hosting
2. **DynamoDB** - Database
3. **S3** - Frontend static hosting
4. **CloudFront** - CDN for frontend

### Monthly Cost Breakdown:

#### 1. Lightsail Container Service
- **Nano** (0.25 vCPU, 0.5 GB RAM): $7/month
- **Micro** (0.5 vCPU, 1 GB RAM): $10/month (recommended for FastAPI)
- **Small** (1 vCPU, 2 GB RAM): $20/month
- **Includes**: Load balancer, SSL certificate, auto-scaling (up to 2 containers)

**Recommended**: Micro plan for 50 users = **$10/month**

#### 2. DynamoDB
- Same as other options: **~$0.70/month**

#### 3. S3 + CloudFront
- Same as other options: **~$0.90/month**

### Total Monthly Cost:

- Lightsail Containers: $10/month
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- **Total: ~$11.60/month**

### Advantages:
✅ **Fixed pricing** - Predictable monthly cost
✅ **Simple setup** - Easy to deploy and manage
✅ **Includes load balancer** - No additional ALB cost
✅ **Includes SSL** - HTTPS certificate included
✅ **Good for small apps** - Perfect for 50 users

### Disadvantages:
⚠️ **Limited scaling** - Only scales to 2 containers on Micro plan
⚠️ **Less flexibility** - Fixed instance sizes
⚠️ **Regional limitations** - Available in fewer regions

---

## Option 3: ECS Fargate Deployment (Flexible)

### Services Required:
1. **ECS Fargate** - Backend container hosting
2. **DynamoDB** - Database
3. **S3** - Frontend static hosting
4. **CloudFront** - CDN for frontend
5. **Application Load Balancer (ALB)** - Load balancing (optional for single container)
6. **Route 53** - DNS (optional, if using custom domain)
7. **ACM** - SSL Certificate (free)

### Monthly Cost Breakdown:

#### 1. ECS Fargate (Backend)
- **Container**: 0.5 vCPU, 1 GB RAM
- **Always-on pricing**: $0.04048/vCPU-hour + $0.004445/GB-hour
- **Cost**: (0.5 × $0.04048 × 730 hours) + (1 × $0.004445 × 730 hours)
- **Monthly**: ~$14.78 + $3.24 = **~$18.02/month**

**Note**: If you run only during business hours (8 hours/day, 22 days/month):
- Cost: ~$4.96/month

#### 2. DynamoDB
**On-Demand Pricing** (Recommended for 50 users):
- Write Request Units: ~2,000 writes/day (50 users × 2 logs/day × 20 operations)
- Read Request Units: ~10,000 reads/day (50 users × 200 reads/user/day)
- **Writes**: 2,000/day × 30 days = 60,000/month = $0.30/month
- **Reads**: 10,000/day × 30 days = 300,000/month = $0.15/month
- **Storage**: ~100 MB (estimated) = $0.25/month
- **Total**: **~$0.70/month**

**Provisioned Capacity** (Alternative):
- 5 Write Capacity Units (WCU) = $0.00065/WCU/hour × 5 × 730 = $2.37/month
- 10 Read Capacity Units (RCU) = $0.00013/RCU/hour × 10 × 730 = $0.95/month
- **Total**: **~$3.32/month**

#### 3. S3 (Frontend Hosting)
- **Storage**: ~50 MB = $0.001/month
- **PUT Requests**: ~10/month (deployments) = $0.00005/month
- **GET Requests**: ~50,000/month (50 users × 1,000 requests/user/month) = $0.0125/month
- **Data Transfer Out**: ~5 GB/month = $0.45/month
- **Total**: **~$0.46/month**

#### 4. CloudFront (CDN)
- **Data Transfer Out**: ~5 GB/month = $0.085/GB × 5 = $0.43/month
- **HTTPS Requests**: ~50,000/month = $0.01/month
- **Total**: **~$0.44/month**

#### 5. Application Load Balancer (ALB) - Optional
- **ALB**: $0.0225/hour × 730 hours = $16.43/month
- **LCU**: ~0.1 LCU average = $0.008/LCU-hour × 0.1 × 730 = $0.58/month
- **Total**: **~$17.01/month** (Optional - can skip for single container)

**Alternative**: Use CloudFront with origin directly to ECS (no ALB needed)

#### 6. Route 53 (DNS) - Optional
- **Hosted Zone**: $0.50/month (if using custom domain)
- **Queries**: ~10,000/month = $0.40/month
- **Total**: **~$0.90/month** (Optional)

#### 7. AWS Certificate Manager (ACM)
- **Free** (SSL certificates)

### Total Monthly Cost:

**Minimum Setup (No ALB, No Route 53)**:
- ECS Fargate: $18.02/month
- DynamoDB: $0.70/month
- S3: $0.46/month
- CloudFront: $0.44/month
- **Total: ~$19.62/month**

**Business Hours Only (8 hours/day, 22 days/month)**:
- ECS Fargate: $4.96/month
- DynamoDB: $0.70/month
- S3: $0.46/month
- CloudFront: $0.44/month
- **Total: ~$6.56/month**

**With ALB and Route 53**:
- ECS Fargate: $18.02/month
- ALB: $17.01/month
- DynamoDB: $0.70/month
- S3: $0.46/month
- CloudFront: $0.44/month
- Route 53: $0.90/month
- **Total: ~$37.53/month**

---

## Option 4: EC2 Deployment (Traditional)

### Services Required:
1. **EC2** - Backend hosting
2. **DynamoDB** - Database
3. **S3** - Frontend static hosting
4. **CloudFront** - CDN
5. **Elastic IP** - Static IP (optional)

### Monthly Cost Breakdown:

#### 1. EC2 Instance
- **t3.micro** (1 vCPU, 1 GB RAM): $0.0104/hour
- **Always-on**: $0.0104 × 730 = **$7.59/month**
- **Business hours only** (8 hours/day, 22 days/month): **$1.83/month**

#### 2. DynamoDB
- Same as Option 1: **~$0.70/month**

#### 3. S3 + CloudFront
- Same as Option 1: **~$0.90/month**

#### 4. Elastic IP (Optional)
- **Free** if attached to running instance

### Total Monthly Cost:

**Always-on**:
- EC2: $7.59/month
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- **Total: ~$9.19/month**

**Business hours only**:
- EC2: $1.83/month
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- **Total: ~$3.43/month**

---

## Option 3: Serverless (Lambda + API Gateway)

### Services Required:
1. **Lambda** - Backend functions
2. **API Gateway** - API endpoint
3. **DynamoDB** - Database
4. **S3** - Frontend static hosting
5. **CloudFront** - CDN

### Monthly Cost Breakdown:

#### 1. Lambda
- **Requests**: ~150,000/month (50 users × 3,000 requests/user/month)
- **Compute**: ~500 ms average, 512 MB memory
- **Requests**: 150,000 × $0.20/1M = $0.03/month
- **Compute**: 150,000 × 0.5s × 0.5 GB = 37.5 GB-seconds
- **Compute**: 37.5 GB-seconds × $0.0000166667/GB-second = $0.0006/month
- **Total**: **~$0.03/month**

#### 2. API Gateway
- **HTTP API**: $1.00/1M requests
- **Requests**: 150,000/month = $0.15/month
- **Data Transfer**: ~1 GB/month = $0.09/GB = $0.09/month
- **Total**: **~$0.24/month**

#### 3. DynamoDB
- Same as Option 1: **~$0.70/month**

#### 4. S3 + CloudFront
- Same as Option 1: **~$0.90/month**

### Total Monthly Cost:

- Lambda: $0.03/month
- API Gateway: $0.24/month
- DynamoDB: $0.70/month
- S3 + CloudFront: $0.90/month
- **Total: ~$1.87/month**

**Note**: Serverless is the cheapest but requires significant code refactoring to work with Lambda.

---

## Cost Comparison Summary

| Option | Always-On | Scale-to-Zero | Notes |
|--------|-----------|---------------|-------|
| **AWS App Runner** ⭐ | $7.99 | $4.71-6.71 | **BEST FOR CONTAINERS** - Simplest setup |
| **Lightsail Containers** | $11.60 | N/A | Fixed pricing, predictable |
| **ECS Fargate** | $19.62 | $6.56 | More control, flexible |
| **EC2** | $9.19 | $3.43 | Cheapest traditional option |
| **Serverless** | $1.87 | $1.87 | Cheapest but requires refactoring |
| **ECS + ALB + Route 53** | $37.53 | N/A | Full production setup |

---

## Additional Costs to Consider

### 1. Data Transfer
- **First 100 GB/month**: Free (within same region)
- **Additional data transfer**: $0.09/GB
- **Estimated**: ~$0-5/month (depending on usage)

### 2. CloudWatch Logs
- **First 5 GB/month**: Free
- **Additional**: $0.50/GB
- **Estimated**: ~$0-2/month

### 3. Backup & Snapshots
- **DynamoDB Backups**: $0.20/GB-month (optional)
- **Estimated**: ~$0-1/month

### 4. Monitoring & Alarms
- **CloudWatch Metrics**: First 10 metrics free
- **Alarms**: $0.10/alarm/month (first 10 free)
- **Estimated**: ~$0/month (within free tier)

### 5. AWS Support
- **Basic**: Free
- **Developer**: $29/month (optional)
- **Business**: $100/month (optional)

---

## Recommended Deployment: AWS App Runner (Option 1) ⭐

### Why AWS App Runner?
1. **Simplest container deployment** - Just push Docker image, everything else is automatic
2. **Zero infrastructure management** - No servers, clusters, or configs to manage
3. **Auto-scaling built-in** - Automatically scales based on traffic
4. **Cost-effective** - Cheaper than ECS Fargate for small apps (~$8/month)
5. **HTTPS included** - SSL certificate management included
6. **Load balancer included** - No ALB needed (saves $17/month)
7. **Works with existing Docker setup** - Uses your existing Dockerfile

### Estimated Total Monthly Cost:

**Always-on (24/7)**:
- Base services: $7.99/month
- Additional costs: ~$2-5/month
- **Total: ~$10-13/month**

**With scale-to-zero** (pauses during inactivity):
- Base services: $4.71-6.71/month
- Additional costs: ~$2-5/month
- **Total: ~$7-12/month**

### Alternative: Lightsail Containers (Option 2)

If you prefer **fixed pricing** and **predictable costs**:
- **Monthly cost**: ~$11.60/month (always-on)
- **Best for**: Small teams, predictable traffic, simple setup
- **Includes**: Load balancer, SSL, auto-scaling (up to 2 containers)

---

## Cost Optimization Tips

1. **Use Business Hours Scheduling**:
   - Run containers only during business hours (8 AM - 6 PM, weekdays)
   - Save ~66% on compute costs
   - Use AWS EventBridge to schedule start/stop

2. **Use DynamoDB On-Demand**:
   - Perfect for unpredictable traffic
   - Pay only for what you use
   - No capacity planning needed

3. **Enable S3 Lifecycle Policies**:
   - Move old logs to Glacier for archival
   - Reduce storage costs

4. **Use CloudFront Caching**:
   - Cache static assets aggressively
   - Reduce S3 data transfer costs

5. **Monitor Usage**:
   - Set up CloudWatch alarms for cost anomalies
   - Review bills regularly
   - Use AWS Cost Explorer for analysis

6. **Reserve Instances** (if using EC2):
   - Save up to 72% with 1-year reservations
   - Only if you're sure about long-term usage

---

## First-Year AWS Free Tier Benefits

### Always Free:
- **DynamoDB**: 25 GB storage, 25 WCU, 25 RCU
- **S3**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests
- **CloudFront**: 1 TB data transfer out, 10,000,000 HTTP/HTTPS requests
- **Lambda**: 1M requests, 400,000 GB-seconds
- **API Gateway**: 1M HTTP API requests

### 12 Months Free:
- **EC2**: 750 hours/month of t2.micro or t3.micro
- **ECS Fargate**: 20 GB-hours/month

### Impact on Costs:
- **First year**: Could reduce costs by ~$5-10/month
- **After first year**: Normal pricing applies

---

## Deployment Steps (Quick Reference)

### Option 1: AWS App Runner (Recommended) ⭐

#### 1. Push Docker Image to ECR:
```bash
# Create ECR repository
aws ecr create-repository --repository-name time-tracking-backend

# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t time-tracking-backend ./backend
docker tag time-tracking-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest
```

#### 2. Create App Runner Service:
```bash
# Create apprunner.yaml configuration file
# Or use AWS Console to create service
# Point to ECR image, set environment variables, configure auto-scaling
```

#### 3. DynamoDB Setup:
```bash
# Tables are created automatically via init_db.py
# Or create manually via AWS Console
```

#### 4. S3 + CloudFront Setup:
```bash
# Build React app
cd frontend
npm run build

# Upload to S3
aws s3 sync build/ s3://your-bucket-name --delete

# Create CloudFront distribution
# Point to S3 bucket origin
```

**App Runner Advantages:**
- No load balancer configuration needed
- No SSL certificate setup needed
- Auto-scaling configured automatically
- HTTPS endpoint provided automatically

### Option 2: Lightsail Containers

#### 1. Push Docker Image to Lightsail:
```bash
# Use Lightsail Console or CLI
# Push container image to Lightsail container service
aws lightsail push-container-image --service-name time-tracking --label backend --image time-tracking-backend:latest
```

#### 2. Create Lightsail Container Service:
- Use AWS Console to create container service
- Select Micro plan ($10/month)
- Configure environment variables
- Set up auto-scaling (up to 2 containers)

#### 3. DynamoDB + S3 + CloudFront:
- Same as Option 1

### Option 3: ECS Fargate

#### 1. ECS Fargate Setup:
```bash
# Build and push Docker image to ECR
aws ecr create-repository --repository-name time-tracking-backend
docker build -t time-tracking-backend ./backend
docker tag time-tracking-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest

# Create ECS cluster and service
aws ecs create-cluster --cluster-name time-tracking-cluster
# Create task definition and service via AWS Console or CLI
```

#### 2. DynamoDB + S3 + CloudFront:
- Same as Option 1

---

## Conclusion

For **50 users**, the recommended deployment is **AWS App Runner** ⭐ with:
- **Monthly cost**: ~$10-13/month (always-on) or ~$7-12/month (with scale-to-zero)
- **Annual cost**: ~$120-156/year (always-on) or ~$84-144/year (with scale-to-zero)

### Why App Runner?
1. **Simplest setup** - Just push Docker image, everything else is automatic
2. **Lowest cost for containers** - Cheaper than ECS Fargate (~$8 vs ~$20)
3. **Zero infrastructure management** - No servers, clusters, or configs
4. **Auto-scaling built-in** - Handles traffic spikes automatically
5. **HTTPS included** - SSL certificate management included
6. **Load balancer included** - No ALB needed (saves $17/month)

### Alternative Options:

**Lightsail Containers** (if you prefer fixed pricing):
- **Monthly cost**: ~$11.60/month
- **Best for**: Predictable costs, simple setup

**ECS Fargate** (if you need more control):
- **Monthly cost**: ~$22-25/month (always-on) or ~$9-12/month (business hours)
- **Best for**: Advanced configurations, custom infrastructure

**EC2** (if you want the cheapest traditional option):
- **Monthly cost**: ~$9/month (always-on) or ~$3/month (business hours)
- **Best for**: Full control, predictable costs

**Serverless** (if you want the absolute cheapest):
- **Monthly cost**: ~$2/month
- **Best for**: Pay-per-use, but requires code refactoring

---

## Notes

- All prices are in USD and based on US East (N. Virginia) region
- Prices may vary by region
- Actual costs may differ based on actual usage patterns
- Consider AWS support plans if you need technical support
- Monitor costs using AWS Cost Explorer and set up billing alerts

