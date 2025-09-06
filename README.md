# 🎫 Event Booking Platform - AWS Deployment Guide

A cloud-native, microservices-based event booking platform deployed on AWS ECS with PostgreSQL, Redis, and Kafka.

## 🚀 Quick Start (5 Minutes)

### Current Running Setup
- **AWS Account**: 376129882286
- **Region**: us-west-2
- **Cluster**: event-booking-platform-cluster
- **Service**: event-booking-platform-service
- **Task Definition**: event-booking-platform-task-fixed:54
- **ALB URL**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
- **Status**: ✅ Currently Running
- **Services**: Frontend, Auth, Catalog, Booking, Payment, Worker, NGINX

### Prerequisites
- AWS Account (Account ID: 376129882286)
- AWS CLI configured with appropriate permissions
- Docker Desktop installed
- PowerShell (Windows) or Bash (Linux/Mac)

### 1. Clone the Repository
```bash
git clone https://github.com/KavindaSandamal/event-booking-platform-cloud.git
cd event-booking-platform-cloud
```

### 2. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-west-2
# Enter output format: json
```

### 3. Deploy Infrastructure
```powershell
# Navigate to terraform directory
cd infrastructure/aws/terraform

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Deploy infrastructure
terraform apply
```

### 4. Build and Push Docker Images
```powershell
# Return to project root
cd ../../..

# Build and push all services
.\scripts\build-enhanced-services.ps1
```

### 5. Deploy Application
```powershell
# Deploy to ECS
aws ecs update-service --cluster "event-booking-platform-cluster" --service "event-booking-platform-service" --force-new-deployment --region us-west-2
```

### 6. Access the Application
- **Frontend**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
- **API Documentation**: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/docs

---

## 📋 Detailed Setup Instructions

### Step 1: AWS Account Setup

1. **Login to AWS Console**
   - Go to https://console.aws.amazon.com
   - Login with your AWS account (376129882286)

2. **Create IAM User for Deployment**
   ```bash
   # Create IAM user with programmatic access
   aws iam create-user --user-name event-booking-deployer
   
   # Attach necessary policies
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonRDSFullAccess
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonVPCFullAccess
   aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AmazonECRFullAccess
   ```

3. **Create Access Keys**
   ```bash
   aws iam create-access-key --user-name event-booking-deployer
   ```

### Step 2: Infrastructure Deployment

1. **Navigate to Terraform Directory**
   ```bash
   cd infrastructure/aws/terraform
   ```

2. **Initialize Terraform**
   ```bash
   terraform init
   ```

3. **Review Configuration**
   ```bash
   # Check variables
   cat variables.tf
   
   # Review main configuration
   cat main.tf
   ```

4. **Deploy Infrastructure**
   ```bash
   # Plan deployment
   terraform plan
   
   # Apply changes
   terraform apply
   # Type 'yes' when prompted
   ```

5. **Note Important Outputs**
   ```bash
   # Get outputs
   terraform output
   
   # Save these values:
   # - RDS endpoint
   # - Redis endpoint
   # - Kafka bootstrap servers
   # - ALB DNS name
   ```

### Step 3: Build and Push Docker Images

1. **Login to ECR**
   ```bash
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 376129882286.dkr.ecr.us-west-2.amazonaws.com
   ```

2. **Build All Services**
   ```powershell
   # Run the build script
   .\scripts\build-enhanced-services.ps1
   ```

   Or build individually:
   ```bash
   # Frontend
   cd services/frontend
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-frontend:latest .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-frontend:latest
   
   # Auth Service
   cd ../auth
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-auth:enhanced .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-auth:enhanced

   # Catalog Service
   cd ../catalog
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-catalog:enhanced .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-catalog:enhanced

   # Booking Service
   cd ../booking
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-booking:enhanced .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-booking:enhanced

   # Payment Service
   cd ../payment
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-payment:enhanced .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-payment:enhanced
   
   # Worker Service
   cd ../worker
   docker build -t 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-worker:enhanced .
   docker push 376129882286.dkr.ecr.us-west-2.amazonaws.com/event-booking-platform-worker:enhanced
   ```

### Step 4: Deploy Application

1. **Register Task Definition**
   ```bash
   aws ecs register-task-definition --cli-input-json file://task-definition-worker-kafka.json --region us-west-2
   ```

2. **Deploy to ECS**
   ```bash
   aws ecs update-service --cluster "event-booking-platform-cluster" --service "event-booking-platform-service" --force-new-deployment --region us-west-2
   ```

3. **Check Deployment Status**
   ```bash
   aws ecs describe-services --cluster "event-booking-platform-cluster" --services "event-booking-platform-service" --region us-west-2 --query "services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,TaskDefinition:taskDefinition}" --output table
   ```

### Step 5: Verify Deployment

1. **Check Service Health**
   ```bash
   # Get ALB DNS name
   aws elbv2 describe-load-balancers --region us-west-2 --query "LoadBalancers[?contains(LoadBalancerName, 'event-booking-platform')].DNSName" --output text
   
   # Test endpoints
   curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/catalog/events
   curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/auth/health
   curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/booking/health
   curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/payment/health
   ```

2. **Access the Application**
   - Open browser and go to: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
   - Register a new account
   - Browse events and make a booking

---

## 🏗️ Architecture Overview

### Services
- **Frontend**: React SPA (Port 3000)
- **Auth Service**: User authentication (Port 8000)
- **Catalog Service**: Event management (Port 8001)
- **Booking Service**: Seat reservations (Port 8002)
- **Payment Service**: Payment processing (Port 8003)
- **Worker Service**: Background tasks (Port 8004)
- **NGINX**: Load balancer and reverse proxy (Port 80)

### Data Layer
- **PostgreSQL**: Primary database (RDS)
- **Redis**: Caching and session storage (ElastiCache)
- **Kafka**: Event streaming (MSK)

### Infrastructure
- **ECS Fargate**: Container orchestration
- **ALB**: Application load balancer
- **VPC**: Network isolation
- **Security Groups**: Network security

---

## 🔧 Configuration

### Environment Variables
The application uses the following key environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@host:5432/eventdb?sslmode=require

# Redis
REDIS_URL=redis://host:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=host1:9096,host2:9096
KAFKA_SASL_USERNAME=kafka
KAFKA_SASL_PASSWORD=kafka123

# Service URLs
AUTH_URL=http://localhost:8000
CATALOG_URL=http://localhost:8001
PAYMENT_SERVICE_URL=http://localhost:8003
```

### AWS Resources Created (Currently Running)
- **VPC**: event-booking-platform-vpc (10.0.0.0/16)
- **RDS PostgreSQL**: event-booking-platform-db.cvcceaki0j7j.us-west-2.rds.amazonaws.com
- **ElastiCache Redis**: event-booking-platform-redis.muj5dn.ng.0001.usw2.cache.amazonaws.com
- **MSK Kafka**: b-1.eventbookingkafkaclust.7xxw9x.c7.kafka.us-west-2.amazonaws.com
- **ECS Cluster**: event-booking-platform-cluster (Fargate)
- **ALB**: event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
- **ECR Repositories**: 
  - event-booking-platform-frontend:latest
  - event-booking-platform-auth:enhanced
  - event-booking-platform-catalog:enhanced
  - event-booking-platform-booking:enhanced
  - event-booking-platform-payment:enhanced
  - event-booking-platform-worker:enhanced
  - event-booking-platform-nginx:latest
- **Security Groups**: Configured for service isolation

---

## 🚨 Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check ECS service logs
   aws logs describe-log-groups --region us-west-2
   aws logs get-log-events --log-group-name "/ecs/event-booking-platform" --log-stream-name "service-name/task-id" --region us-west-2
   ```

2. **Database Connection Issues**
   ```bash
   # Check RDS status
   aws rds describe-db-instances --region us-west-2 --query "DBInstances[?contains(DBInstanceIdentifier, 'event-booking-platform')].{DBInstanceIdentifier:DBInstanceIdentifier,DBInstanceStatus:DBInstanceStatus,Endpoint:Endpoint.Address}" --output table
   ```

3. **Image Pull Errors**
   ```bash
   # Check ECR images
   aws ecr describe-images --repository-name event-booking-platform-frontend --region us-west-2
   ```

4. **Load Balancer Issues**
   ```bash
   # Check ALB status
   aws elbv2 describe-load-balancers --region us-west-2 --query "LoadBalancers[?contains(LoadBalancerName, 'event-booking-platform')].{LoadBalancerName:LoadBalancerName,State:State,DNSName:DNSName}" --output table
   ```

### Health Checks
```bash
# Service health endpoints
curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/auth/health
curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/catalog/health
curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/booking/health
curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/payment/health
```

---

## 📊 Monitoring

### CloudWatch Logs
- Log Group: `/ecs/event-booking-platform`
- Log Streams: `service-name/task-id`

### ECS Console
- Cluster: `event-booking-platform-cluster`
- Service: `event-booking-platform-service`
- Tasks: View running tasks and their status

### Application Metrics
- Response times
- Error rates
- Throughput
- Resource utilization

---

## 🔄 Updates and Maintenance

### Updating Services
1. **Build new images**
   ```bash
   .\scripts\build-enhanced-services.ps1
   ```

2. **Deploy updates**
   ```bash
   aws ecs update-service --cluster "event-booking-platform-cluster" --service "event-booking-platform-service" --force-new-deployment --region us-west-2
   ```

3. **Check deployment status**
   ```bash
   aws ecs describe-services --cluster "event-booking-platform-cluster" --services "event-booking-platform-service" --region us-west-2 --query "services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,TaskDefinition:taskDefinition}" --output table
   ```

### Scaling Services
```bash
# Update desired count
aws ecs update-service --cluster "event-booking-platform-cluster" --service "event-booking-platform-service" --desired-count 3 --region us-west-2
```

### Backup and Recovery
- RDS automated backups are enabled
- Redis snapshots can be configured
- ECR images are versioned

---

## 💰 Cost Optimization

### AWS Free Tier Usage
- **EC2**: t3.micro instances
- **RDS**: db.t3.micro (750 hours/month)
- **ElastiCache**: cache.t3.micro (750 hours/month)
- **EBS**: 30GB General Purpose storage
- **Data Transfer**: 1GB/month outbound

### Estimated Monthly Cost
- **RDS**: ~$15-20/month
- **ElastiCache**: ~$15-20/month
- **ECS Fargate**: ~$10-15/month
- **ALB**: ~$20/month
- **Total**: ~$60-75/month

---

## 📚 Additional Resources

### Documentation
- [Implementation Document](IMPLEMENTATION_DOCUMENT.md)
- [Architecture Overview](ARCHITECTURE.md)
- [JWT Security Guide](JWT_SESSION_MANAGEMENT.md)

### API Documentation
- Swagger UI: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/docs
- ReDoc: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/redoc

### Support
- Check CloudWatch logs for errors
- Review ECS service events
- Monitor ALB target health

---

## 🎯 Success Criteria

After successful deployment, you should be able to:
- ✅ Access the frontend at the ALB URL
- ✅ Register a new user account
- ✅ Browse available events
- ✅ Create a booking
- ✅ Process a payment
- ✅ View booking history
- ✅ Download receipts

---

**🎉 Congratulations! Your Event Booking Platform is now running on AWS!**

For any issues or questions, check the troubleshooting section or review the CloudWatch logs for detailed error information.