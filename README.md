# Event Booking Platform - AWS Cloud Deployment

A modern, scalable event booking platform built with microservices architecture, deployed on AWS ECS with PostgreSQL, Redis, and Kafka.

## 🚀 Quick Start

**Live Application**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/

## 📋 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with your credentials
- Docker installed locally
- PowerShell (Windows) or Bash (Linux/Mac)
- Git

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   NGINX         │    │   Auth Service  │
│   (React)       │◄───┤   Load Balancer │◄───┤   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼───────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │ Catalog       │ │ Booking   │ │ Payment     │
        │ Service       │ │ Service   │ │ Service     │
        └───────────────┘ └───────────┘ └─────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   PostgreSQL (RDS)    │
                    │   Redis (ElastiCache) │
                    │   Kafka (MSK)         │
                    └───────────────────────┘
```

## 🛠️ AWS Setup

### 1. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region (us-west-2), and output format (json)
```

### 2. Create ECR Repositories

```bash
# Create repositories for all services
aws ecr create-repository --repository-name event-booking-platform-frontend --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-auth --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-catalog --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-booking --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-payment --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-worker --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-nginx --region us-west-2
```

### 3. Deploy Infrastructure with Terraform

```bash
cd infrastructure/aws/terraform
terraform init
terraform plan
terraform apply
```

This creates:
- VPC with public/private subnets
- ECS Cluster
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- MSK Kafka cluster
- Application Load Balancer
- Security Groups
- IAM roles

## 🐳 Build and Push Docker Images

### Option 1: Build All Services (Recommended)

```powershell
# Run the automated build script
.\build-enhanced-services.ps1
```

### Option 2: Build Individual Services

```bash
# Get ECR login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 376129882286.dkr.ecr.us-west-2.amazonaws.com

# Build and push each service
cd services/frontend
docker build -t event-booking-platform-frontend:latest .
docker tag event-booking-platform-frontend:latest 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-frontend:latest
docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-frontend:latest

# Repeat for other services...
```

## 🚀 Deploy to ECS

### 1. Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://task-definition-worker-kafka.json --region us-west-2
```

### 2. Create ECS Service

```bash
aws ecs create-service \
  --cluster event-booking-platform-cluster \
  --service-name event-booking-platform-service \
  --task-definition event-booking-platform-task-fixed:47 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-west-2:376129882286:targetgroup/event-booking-platform-nginx-tg/12345,containerName=nginx,containerPort=80" \
  --region us-west-2
```

### 3. Force New Deployment (if updating)

```bash
aws ecs update-service \
  --cluster event-booking-platform-cluster \
  --service event-booking-platform-service \
  --force-new-deployment \
  --region us-west-2
```

## 🔧 Configuration

### Environment Variables

The application uses the following key environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@your-rds-endpoint:5432/eventdb?sslmode=require

# Redis
REDIS_URL=redis://your-redis-endpoint:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=your-kafka-endpoint:9092
KAFKA_SASL_USERNAME=your-username
KAFKA_SASL_PASSWORD=your-password

# Service URLs
AUTH_URL=http://auth:8001
CATALOG_URL=http://catalog:8002
BOOKING_SERVICE_URL=http://booking:8002
PAYMENT_SERVICE_URL=http://payment:8003
```

## 📊 Monitoring

### Access Grafana Dashboard

```bash
# Get the Grafana URL from ALB
aws elbv2 describe-load-balancers --names event-booking-platform-alb --region us-west-2
```

### View Application Logs

```bash
# View logs for specific service
aws logs tail /aws/ecs/event-booking-platform --follow --region us-west-2
```

## 🧪 Testing the Application

1. **Access the Application**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/
2. **Register a new account**
3. **Browse events**
4. **Create a booking**
5. **Process payment**
6. **View your bookings**

## 🔍 Troubleshooting

### Common Issues

1. **Service Communication Errors**
   ```bash
   # Check if services are running
   aws ecs describe-services --cluster event-booking-platform-cluster --services event-booking-platform-service --region us-west-2
   ```

2. **Database Connection Issues**
   ```bash
   # Check RDS status
   aws rds describe-db-instances --db-instance-identifier event-booking-platform-db --region us-west-2
   ```

3. **Image Pull Errors**
   ```bash
   # Check ECR images
   aws ecr describe-images --repository-name event-booking-platform-frontend --region us-west-2
   ```

### View Service Logs

```bash
# Get log group names
aws logs describe-log-groups --log-group-name-prefix /aws/ecs/event-booking-platform --region us-west-2

# View specific service logs
aws logs tail /aws/ecs/event-booking-platform-auth --follow --region us-west-2
```

## 📁 Project Structure

```
event-booking-platform/
├── services/                 # Microservices
│   ├── frontend/            # React frontend
│   ├── auth/                # Authentication service
│   ├── catalog/             # Event catalog service
│   ├── booking/             # Booking service
│   ├── payment/             # Payment service
│   ├── worker/              # Background worker
│   └── nginx/               # Load balancer
├── infrastructure/          # Infrastructure as Code
│   ├── aws/terraform/       # Terraform configurations
│   └── kubernetes/          # Kubernetes manifests
├── scripts/                 # Deployment scripts
├── task-definition-worker-kafka.json  # ECS task definition
└── docker-compose.yml       # Local development
```

## 🚀 Quick Deployment Commands

```bash
# 1. Build and push all images
.\build-enhanced-services.ps1

# 2. Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition-worker-kafka.json --region us-west-2

# 3. Deploy to ECS
aws ecs update-service --cluster event-booking-platform-cluster --service event-booking-platform-service --force-new-deployment --region us-west-2

# 4. Check deployment status
aws ecs describe-services --cluster event-booking-platform-cluster --services event-booking-platform-service --region us-west-2
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Verify all services are running in ECS console
4. Ensure all environment variables are correctly set

## 🎯 Features

- ✅ User Authentication & Authorization
- ✅ Event Catalog Management
- ✅ Booking System
- ✅ Payment Processing
- ✅ PDF Ticket Generation
- ✅ Real-time Notifications
- ✅ Scalable Microservices Architecture
- ✅ Cloud-Native Deployment
- ✅ Monitoring & Logging
- ✅ Circuit Breaker Pattern
- ✅ Event-Driven Architecture

---

**Live Application**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/

**GitHub Repository**: https://github.com/KavindaSandamal/event-booking-platform-cloud.git
