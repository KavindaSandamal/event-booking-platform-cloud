# 🚀 Quick Start Guide - Event Booking Platform

This guide will get you up and running with the Event Booking Platform on AWS using Kubernetes (EKS) in under 30 minutes.

## 📋 Prerequisites Checklist

- [ ] AWS Account with free tier eligibility
- [ ] AWS CLI installed and configured
- [ ] Terraform installed
- [ ] kubectl installed
- [ ] eksctl installed
- [ ] Docker installed

## ⚡ 5-Minute Setup

### 1. Clone and Configure
```bash
git clone <your-repo-url>
cd event-booking-platform

# Copy environment template
cp env.cloud.example .env

# Edit with your AWS details
nano .env
```

**Required Environment Variables:**
```bash
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=your_aws_account_id
DB_PASSWORD=your_secure_password
JWT_SECRET=your_jwt_secret
RABBITMQ_PASSWORD=your_rabbitmq_password
REDIS_PASSWORD=your_redis_password
```

### 2. Deploy Infrastructure
```bash
cd infrastructure/aws/terraform

# Initialize and deploy
terraform init
terraform apply -var="aws_account_id=YOUR_ACCOUNT_ID" -var="aws_region=us-west-2"
```

### 3. Deploy Application
```bash
# Configure kubectl
aws eks update-kubeconfig --region us-west-2 --name event-booking-platform-cluster

# Deploy to Kubernetes
./scripts/deploy-kubernetes.sh
```

### 4. Access Your Application
```bash
# Get the application URL
kubectl get ingress -n event-booking-platform

# Access the application
curl http://your-alb-dns-name
```

## 🎯 What You Get

### ✅ Cloud-Native Features
- **Microservices Architecture**: 5 independent services
- **Kubernetes Orchestration**: Auto-scaling and self-healing
- **Load Balancing**: NGINX Ingress Controller
- **Service Discovery**: Kubernetes DNS
- **Health Checks**: Liveness and readiness probes
- **Horizontal Pod Autoscaling**: Based on CPU/Memory usage

### ✅ AWS Free Tier Services
- **EKS Cluster**: Managed Kubernetes
- **RDS PostgreSQL**: db.t3.micro (20GB)
- **ElastiCache Redis**: cache.t3.micro
- **Amazon MQ**: mq.t3.micro (RabbitMQ)
- **ECR**: Container registry
- **ALB**: Application Load Balancer

### ✅ Production-Ready Features
- **Circuit Breakers**: Fault tolerance
- **Retry Mechanisms**: Resilient communication
- **Security Headers**: HTTPS, CORS, CSP
- **Rate Limiting**: DDoS protection
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured JSON logs

## 🔧 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Auth Service  │    │ Catalog Service │
│   (React SPA)   │    │   (JWT Auth)    │    │   (Events)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   NGINX Ingress │
                    │   (Load Balancer)│
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Booking Service │    │ Payment Service │    │ Worker Service  │
│ (Reservations)  │    │ (Transactions)  │    │ (Background)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Layer    │
                    │ PostgreSQL +    │
                    │ Redis + RabbitMQ│
                    └─────────────────┘
```

## 📊 Monitoring Dashboard

Access Grafana at `http://your-alb-dns-name:3000` to view:
- Request rates and response times
- Error rates and success rates
- Resource utilization
- Service health status
- Circuit breaker states

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl http://your-alb-dns-name/health
```

### 2. API Documentation
```bash
# Open in browser
http://your-alb-dns-name/docs
```

### 3. Load Testing
```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 http://your-alb-dns-name/
```

### 4. Check Auto-scaling
```bash
# Watch HPA
kubectl get hpa -n event-booking-platform -w

# Scale manually
kubectl scale deployment booking-service --replicas=5 -n event-booking-platform
```

## 🛠️ Common Commands

### View Logs
```bash
kubectl logs -f deployment/auth-service -n event-booking-platform
```

### Check Pod Status
```bash
kubectl get pods -n event-booking-platform
```

### Scale Services
```bash
kubectl scale deployment booking-service --replicas=3 -n event-booking-platform
```

### Update Application
```bash
# Build new images
./scripts/build-and-push-images.sh

# Restart deployments
kubectl rollout restart deployment/auth-service -n event-booking-platform
```

## 💰 Cost Monitoring

### Check AWS Costs
```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget '{
    "BudgetName": "Event-Booking-Budget",
    "BudgetLimit": {"Amount": "5", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

### Free Tier Usage
- **EC2**: 750 hours/month (t3.micro)
- **RDS**: 750 hours/month (db.t3.micro)
- **ElastiCache**: 750 hours/month (cache.t3.micro)
- **EBS**: 30 GB storage
- **Data Transfer**: 1 GB/month

## 🚨 Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name> -n event-booking-platform
kubectl logs <pod-name> -n event-booking-platform
```

### Service Not Accessible
```bash
kubectl get ingress -n event-booking-platform
kubectl get services -n event-booking-platform
```

### Database Connection Issues
```bash
kubectl exec -it <pod-name> -n event-booking-platform -- nslookup your-rds-endpoint
```

## 🎓 Learning Objectives Achieved

By completing this setup, you've learned:

1. **Cloud-Native Architecture**: Microservices, containers, orchestration
2. **AWS Services**: EKS, RDS, ElastiCache, ECR, ALB
3. **Kubernetes**: Deployments, Services, Ingress, HPA
4. **DevOps Practices**: Infrastructure as Code, CI/CD, monitoring
5. **Security**: Secrets management, network policies, RBAC
6. **Scalability**: Auto-scaling, load balancing, circuit breakers

## 📚 Next Steps

1. **Custom Domain**: Set up your own domain name
2. **SSL Certificates**: Enable HTTPS with Let's Encrypt
3. **CI/CD Pipeline**: Automate deployments with GitHub Actions
4. **Advanced Monitoring**: Set up alerting and dashboards
5. **Security Hardening**: Implement network policies and RBAC
6. **Performance Tuning**: Optimize based on monitoring data

## 🆘 Getting Help

- **Documentation**: Check the full [AWS Setup Guide](AWS_SETUP_GUIDE.md)
- **Issues**: Create an issue in the repository
- **Community**: Join our Discord server
- **Tutorials**: Watch our video tutorials

---

**Happy Learning! 🎉**

This setup demonstrates modern cloud-native practices while staying within AWS free tier limits, perfect for educational purposes.
