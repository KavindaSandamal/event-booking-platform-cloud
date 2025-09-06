# CI/CD Guide - Event Booking Platform

This guide explains the GitHub Actions CI/CD setup for the Event Booking Platform.

## 🚀 Workflows Overview

### 1. Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Jobs:**
1. **build-and-test**: Runs tests and linting
2. **build-and-push**: Builds and pushes Docker images to ECR
3. **deploy**: Deploys to ECS
4. **security-scan**: Runs security vulnerability scans

### 2. Infrastructure Pipeline (`.github/workflows/infrastructure.yml`)

**Triggers:**
- Changes to `infrastructure/` directory
- Manual workflow dispatch

**Jobs:**
1. **terraform-plan**: Plans infrastructure changes
2. **terraform-apply**: Applies infrastructure changes

### 3. Monitoring Pipeline (`.github/workflows/monitoring.yml`)

**Triggers:**
- Every 15 minutes (scheduled)
- Manual workflow dispatch

**Jobs:**
1. **health-check**: Checks application and infrastructure health
2. **performance-test**: Runs performance tests (manual)
3. **security-scan**: Runs security scans (manual)

### 4. Database Pipeline (`.github/workflows/database.yml`)

**Triggers:**
- Changes to database models/schemas
- Manual workflow dispatch

**Jobs:**
1. **database-migration**: Runs database migrations

### 5. Rollback Pipeline (`.github/workflows/rollback.yml`)

**Triggers:**
- Manual workflow dispatch only

**Jobs:**
1. **validate-rollback**: Validates rollback target
2. **execute-rollback**: Executes the rollback
3. **rollback-failed**: Handles failed rollback attempts

## 🔧 Setup Instructions

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
```

### 2. Required AWS Permissions

Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:*",
                "ecs:*",
                "iam:PassRole",
                "elasticloadbalancing:*",
                "rds:*",
                "elasticache:*",
                "kafka:*",
                "logs:*",
                "cloudwatch:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. ECR Repositories

Ensure these ECR repositories exist:

```bash
aws ecr create-repository --repository-name event-booking-platform-frontend --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-auth --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-catalog --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-booking --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-payment --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-worker --region us-west-2
aws ecr create-repository --repository-name event-booking-platform-nginx --region us-west-2
```

## 🔄 Workflow Execution

### Automatic Deployments

1. **Push to main branch** → Full CI/CD pipeline runs
2. **Push to develop branch** → Tests run, no deployment
3. **Pull request to main** → Tests run, no deployment

### Manual Deployments

1. Go to Actions tab in GitHub
2. Select the workflow you want to run
3. Click "Run workflow"
4. Choose branch and parameters
5. Click "Run workflow"

### Rollback Process

1. Go to Actions → Rollback Deployment
2. Click "Run workflow"
3. Enter task definition revision (or "previous")
4. Type "ROLLBACK" in confirmation field
5. Click "Run workflow"

## 📊 Monitoring and Alerts

### Health Checks

The monitoring workflow runs every 15 minutes and checks:
- ECS service status
- Application health endpoints
- Database connectivity
- Redis connectivity
- Kafka connectivity

### Performance Testing

Manual performance tests using k6:
- Load testing with 10 concurrent users
- Response time monitoring
- Error rate tracking

### Security Scanning

- **Trivy**: Vulnerability scanning for containers
- **OWASP ZAP**: Web application security testing
- **CodeQL**: Static code analysis

## 🛠️ Customization

### Adding New Services

1. Add service to `ci-cd.yml` build-and-push job
2. Update task definition in deploy job
3. Add ECR repository creation to setup

### Modifying Deployment Strategy

Edit the `deploy` job in `ci-cd.yml`:
- Change deployment strategy
- Add pre/post deployment hooks
- Modify health check parameters

### Adding Tests

1. Add test files to service directories
2. Update test commands in `build-and-test` job
3. Add test result reporting

## 🚨 Troubleshooting

### Common Issues

1. **ECR Push Fails**
   - Check AWS credentials
   - Verify ECR repositories exist
   - Check IAM permissions

2. **ECS Deployment Fails**
   - Check task definition validity
   - Verify ECS cluster exists
   - Check service configuration

3. **Health Checks Fail**
   - Check application logs
   - Verify ALB configuration
   - Check security groups

### Debugging Steps

1. Check workflow logs in GitHub Actions
2. Check ECS service logs in CloudWatch
3. Verify AWS resource status
4. Check application health endpoints

## 📈 Best Practices

1. **Branch Protection**: Enable branch protection rules for main branch
2. **Required Checks**: Require status checks before merging
3. **Review Process**: Require pull request reviews
4. **Secrets Management**: Use GitHub Secrets for sensitive data
5. **Monitoring**: Set up CloudWatch alarms for critical metrics
6. **Backup**: Regular database backups before deployments
7. **Testing**: Comprehensive test coverage before deployment

## 🔗 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Terraform Documentation](https://www.terraform.io/docs)

## 📞 Support

For CI/CD issues:
1. Check GitHub Actions logs
2. Review AWS CloudWatch logs
3. Verify all secrets are configured
4. Check AWS resource permissions
