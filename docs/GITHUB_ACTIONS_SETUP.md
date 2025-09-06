# GitHub Actions CI/CD Setup Guide

## 🚀 Quick Setup Steps

### 1. Configure GitHub Secrets

Go to your GitHub repository: https://github.com/KavindaSandamal/event-booking-platform-cloud

**Navigate to:** Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

```
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
DATABASE_URL=postgresql://postgres:your_password@your-rds-endpoint:5432/eventdb?sslmode=require
```

### 2. Verify ECR Repositories

Ensure these ECR repositories exist in your AWS account:

```bash
# Check existing repositories
aws ecr describe-repositories --region us-west-2

# Create missing repositories if needed
aws ecr create-repository --repository-name event-booking-platform-frontend --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-auth --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-catalog --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-booking --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-payment --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-worker --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-nginx --region us-west-2
```

### 3. Test the CI/CD Pipeline

**Option A: Automatic Trigger**
- Make a small change to any file
- Commit and push to main branch
- Watch the Actions tab in GitHub

**Option B: Manual Trigger**
- Go to Actions tab in GitHub
- Select "Event Booking Platform CI/CD"
- Click "Run workflow"
- Choose "main" branch
- Click "Run workflow"

### 4. Monitor the Deployment

1. **Check GitHub Actions:**
   - Go to Actions tab
   - Click on the running workflow
   - Monitor each step

2. **Check AWS ECS:**
   ```bash
   aws ecs describe-services --cluster event-booking-platform-cluster --services event-booking-platform-service --region us-west-2
   ```

3. **Check Application:**
   - Visit: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
   - Test the application functionality

## 🔧 Workflow Details

### Main CI/CD Pipeline (ci-cd.yml)

**Triggers:**
- Push to main/develop branches
- Pull requests to main

**Stages:**
1. **Build & Test** - Runs tests and linting
2. **Build & Push** - Builds Docker images and pushes to ECR
3. **Deploy** - Updates ECS service with new images
4. **Security Scan** - Runs vulnerability scans

### Infrastructure Pipeline (infrastructure.yml)

**Triggers:**
- Changes to infrastructure/ directory
- Manual dispatch

**Stages:**
1. **Terraform Plan** - Plans infrastructure changes
2. **Terraform Apply** - Applies changes to AWS

### Monitoring Pipeline (monitoring.yml)

**Triggers:**
- Every 15 minutes (scheduled)
- Manual dispatch

**Features:**
- Health checks
- Performance testing
- Security scanning

## 🛠️ Troubleshooting

### Common Issues

1. **ECR Push Fails**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Check ECR permissions
   aws ecr get-login-password --region us-west-2
   ```

2. **ECS Deployment Fails**
   ```bash
   # Check task definition
   aws ecs describe-task-definition --task-definition event-booking-platform-task-fixed --region us-west-2
   
   # Check service status
   aws ecs describe-services --cluster event-booking-platform-cluster --services event-booking-platform-service --region us-west-2
   ```

3. **Health Checks Fail**
   ```bash
   # Check application logs
   aws logs tail /aws/ecs/event-booking-platform --follow --region us-west-2
   ```

### Debug Commands

```bash
# Check GitHub Actions status
gh run list --repo KavindaSandamal/event-booking-platform-cloud

# Check ECS service health
aws ecs describe-services --cluster event-booking-platform-cluster --services event-booking-platform-service --region us-west-2 --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount}'

# Check application health
curl -f http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/health
```

## 📊 Monitoring Dashboard

### GitHub Actions Dashboard
- **URL:** https://github.com/KavindaSandamal/event-booking-platform-cloud/actions
- **Features:** Workflow status, logs, artifacts

### AWS CloudWatch
- **Logs:** /aws/ecs/event-booking-platform
- **Metrics:** ECS service metrics
- **Alarms:** Set up for service health

### Application Health
- **URL:** http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
- **Health Check:** /health endpoint

## 🔄 Rollback Process

If deployment fails:

1. **Go to GitHub Actions**
2. **Select "Rollback Deployment" workflow**
3. **Click "Run workflow"**
4. **Enter rollback target (or "previous")**
5. **Type "ROLLBACK" in confirmation**
6. **Click "Run workflow"**

## 📈 Next Steps

1. **Set up monitoring alerts** in AWS CloudWatch
2. **Configure branch protection rules** in GitHub
3. **Add more comprehensive tests** for each service
4. **Set up staging environment** for testing
5. **Configure automated backups** for database

## 🔗 Useful Links

- **GitHub Repository:** https://github.com/KavindaSandamal/event-booking-platform-cloud
- **GitHub Actions:** https://github.com/KavindaSandamal/event-booking-platform-cloud/actions
- **Live Application:** http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
- **AWS Console:** https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/clusters

## 📞 Support

If you encounter issues:
1. Check GitHub Actions logs
2. Check AWS CloudWatch logs
3. Verify all secrets are configured
4. Check AWS resource permissions
5. Review the troubleshooting section above
