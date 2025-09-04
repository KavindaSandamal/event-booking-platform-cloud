# 🚀 AWS Cloud-Native Deployment Guide

This comprehensive guide will help you deploy the Event Booking Platform to AWS using Kubernetes (EKS) with free tier optimization.

## 📋 Prerequisites

### 1. AWS Account Setup
- Create an AWS account at [aws.amazon.com](https://aws.amazon.com)
- Complete the account verification process
- Set up billing alerts to monitor costs
- Enable free tier notifications

### 2. Required Tools Installation

#### AWS CLI
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

#### Terraform
```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version
```

#### kubectl
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

#### eksctl
```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

#### Docker
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

## 🔧 AWS Configuration

### 1. Configure AWS CLI
```bash
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-west-2`)
- Default output format (`json`)

### 2. Create IAM User (Recommended)
```bash
# Create IAM user for programmatic access
aws iam create-user --user-name event-booking-deployer

# Attach necessary policies
aws iam attach-user-policy --user-name event-booking-deployer --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access keys
aws iam create-access-key --user-name event-booking-deployer
```

## 🏗️ Infrastructure Deployment

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd event-booking-platform
```

### 2. Configure Environment Variables
```bash
# Copy environment template
cp env.cloud.example .env

# Edit with your values
nano .env
```

Required variables:
```bash
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=your_aws_account_id

# Database
DB_PASSWORD=your_secure_password

# JWT
JWT_SECRET=your_super_secure_jwt_secret

# RabbitMQ
RABBITMQ_PASSWORD=your_rabbitmq_password

# Redis
REDIS_PASSWORD=your_redis_password
```

### 3. Deploy Infrastructure with Terraform
```bash
cd infrastructure/aws/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="aws_account_id=YOUR_ACCOUNT_ID" -var="aws_region=us-west-2"

# Apply infrastructure
terraform apply -var="aws_account_id=YOUR_ACCOUNT_ID" -var="aws_region=us-west-2"
```

### 4. Configure kubectl for EKS
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name event-booking-platform-cluster

# Verify connection
kubectl get nodes
```

## 🐳 Container Deployment

### 1. Build and Push Docker Images
```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Build and push services
./scripts/build-and-push-images.sh
```

### 2. Deploy to Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n event-booking-platform
kubectl get services -n event-booking-platform
```

## 📊 Monitoring Setup

### 1. Install Prometheus and Grafana
```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Get Grafana password
kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

### 2. Access Monitoring Dashboards
```bash
# Port forward to access Grafana
kubectl port-forward --namespace monitoring svc/prometheus-grafana 3000:80

# Access Grafana at http://localhost:3000
# Username: admin
# Password: (from previous step)
```

## 🌐 Application Access

### 1. Get Load Balancer URL
```bash
# Get ALB DNS name
kubectl get ingress -n event-booking-platform

# Or from Terraform output
cd infrastructure/aws/terraform
terraform output alb_dns_name
```

### 2. Access Application
- **Frontend**: `http://your-alb-dns-name`
- **API Documentation**: `http://your-alb-dns-name/docs`
- **Grafana**: `http://your-alb-dns-name:3000`
- **Prometheus**: `http://your-alb-dns-name:9090`

## 💰 Cost Optimization (Free Tier)

### AWS Free Tier Limits
- **EC2**: 750 hours/month of t2.micro instances
- **RDS**: 750 hours/month of db.t3.micro
- **ElastiCache**: 750 hours/month of cache.t3.micro
- **EBS**: 30 GB of General Purpose (gp2) storage
- **Data Transfer**: 1 GB/month out

### Cost Monitoring
```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget '{
    "BudgetName": "Event-Booking-Platform-Budget",
    "BudgetLimit": {
      "Amount": "10",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

## 🔒 Security Best Practices

### 1. Network Security
- All services run in private subnets
- Database and cache are not publicly accessible
- Security groups restrict traffic

### 2. Secrets Management
```bash
# Update secrets in Kubernetes
kubectl create secret generic app-secrets \
  --from-literal=DB_PASSWORD=your_password \
  --from-literal=JWT_SECRET=your_jwt_secret \
  -n event-booking-platform
```

### 3. SSL/TLS Setup
```bash
# Install cert-manager for SSL certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
kubectl apply -f infrastructure/kubernetes/ssl-issuer.yaml
```

## 🚀 Scaling and Performance

### 1. Horizontal Pod Autoscaling
```bash
# Check HPA status
kubectl get hpa -n event-booking-platform

# Scale manually if needed
kubectl scale deployment auth-service --replicas=3 -n event-booking-platform
```

### 2. Cluster Autoscaling
```bash
# Install cluster autoscaler
kubectl apply -f infrastructure/kubernetes/cluster-autoscaler.yaml
```

## 🧪 Testing and Validation

### 1. Health Checks
```bash
# Check all pods are running
kubectl get pods -n event-booking-platform

# Check service endpoints
kubectl get endpoints -n event-booking-platform

# Test application health
curl http://your-alb-dns-name/health
```

### 2. Load Testing
```bash
# Install hey for load testing
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 http://your-alb-dns-name/
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Pods Not Starting
```bash
# Check pod logs
kubectl logs -f deployment/auth-service -n event-booking-platform

# Check pod events
kubectl describe pod <pod-name> -n event-booking-platform
```

#### 2. Database Connection Issues
```bash
# Check RDS endpoint
kubectl exec -it <pod-name> -n event-booking-platform -- nslookup your-rds-endpoint

# Test database connectivity
kubectl exec -it <pod-name> -n event-booking-platform -- psql -h your-rds-endpoint -U postgres -d eventdb
```

#### 3. Service Discovery Issues
```bash
# Check DNS resolution
kubectl exec -it <pod-name> -n event-booking-platform -- nslookup auth-service

# Check service endpoints
kubectl get endpoints -n event-booking-platform
```

## 📚 Additional Resources

### Documentation
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Monitoring and Observability
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AWS CloudWatch](https://docs.aws.amazon.com/cloudwatch/)

### Security
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)

## 🎯 Next Steps

1. **Domain Setup**: Configure your domain to point to the ALB
2. **SSL Certificates**: Set up HTTPS with Let's Encrypt
3. **CI/CD Pipeline**: Implement automated deployment
4. **Backup Strategy**: Set up automated database backups
5. **Monitoring Alerts**: Configure alerting for critical metrics
6. **Performance Tuning**: Optimize based on monitoring data

## 💡 Tips for Educational Use

1. **Start Small**: Begin with minimal resources and scale up
2. **Monitor Costs**: Set up billing alerts and check costs daily
3. **Use Spot Instances**: For non-production workloads
4. **Clean Up**: Always delete resources when not in use
5. **Document Everything**: Keep notes of your configuration and learnings

---

**Happy Learning! 🎓**

This setup provides a production-ready, cloud-native architecture that demonstrates modern DevOps practices while staying within AWS free tier limits.
