#!/bin/bash

# AWS Cloud-Native Deployment Script for Event Booking Platform
# This script deploys the entire platform to AWS using Terraform and ECS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="event-booking-platform"
AWS_REGION="us-west-2"
TERRAFORM_DIR="infrastructure/aws/terraform"

echo -e "${BLUE}🚀 Starting AWS Cloud-Native Deployment${NC}"
echo "================================================"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check if AWS CLI is installed
    AWS_CLI_PATH=""
    if command -v aws &> /dev/null; then
        AWS_CLI_PATH="aws"
    elif [ -f "/c/Program Files/Amazon/AWSCLIV2/aws.exe" ]; then
        AWS_CLI_PATH="/c/Program Files/Amazon/AWSCLIV2/aws.exe"
    elif [ -f "C:/Program Files/Amazon/AWSCLIV2/aws.exe" ]; then
        AWS_CLI_PATH="C:/Program Files/Amazon/AWSCLIV2/aws.exe"
    elif [ -f "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe" ]; then
        AWS_CLI_PATH="C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe"
    else
        echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! $AWS_CLI_PATH sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure'${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Get AWS Account ID
get_aws_account_id() {
    echo -e "${YELLOW}🔍 Getting AWS Account ID...${NC}"
    AWS_ACCOUNT_ID=$($AWS_CLI_PATH sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✅ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
}

# Build and push Docker images to ECR
build_and_push_images() {
    echo -e "${YELLOW}🐳 Building and pushing Docker images to ECR...${NC}"
    
    # Login to ECR
    $AWS_CLI_PATH ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build and push each service
    services=("nginx" "auth" "catalog" "booking" "payment" "frontend")
    
    for service in "${services[@]}"; do
        echo -e "${BLUE}Building ${service}...${NC}"
        
        if [ "$service" = "nginx" ]; then
            docker build -t $PROJECT_NAME-$service:latest ./infrastructure/nginx/
        elif [ "$service" = "frontend" ]; then
            docker build -t $PROJECT_NAME-$service:latest ./frontend/
        else
            docker build -t $PROJECT_NAME-$service:latest ./services/$service/
        fi
        
        # Tag for ECR
        docker tag $PROJECT_NAME-$service:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$service:latest
        
        # Push to ECR
        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$service:latest
        
        echo -e "${GREEN}✅ ${service} image pushed successfully${NC}"
    done
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    echo -e "${YELLOW}🏗️ Deploying infrastructure with Terraform...${NC}"
    
    cd $TERRAFORM_DIR
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -var="aws_account_id=$AWS_ACCOUNT_ID" -var="aws_region=$AWS_REGION"
    
    # Apply deployment
    terraform apply -auto-approve -var="aws_account_id=$AWS_ACCOUNT_ID" -var="aws_region=$AWS_REGION"
    
    # Get outputs
    ALB_DNS=$(terraform output -raw alb_dns_name)
    ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
    echo -e "${GREEN}🌐 Application Load Balancer: http://$ALB_DNS${NC}"
    echo -e "${GREEN}📊 ECS Cluster: $ECS_CLUSTER${NC}"
    
    cd ../..
}

# Update ECS service
update_ecs_service() {
    echo -e "${YELLOW}🔄 Updating ECS service...${NC}"
    
    # Force new deployment
    $AWS_CLI_PATH ecs update-service \
        --cluster $PROJECT_NAME-cluster \
        --service $PROJECT_NAME-service \
        --force-new-deployment \
        --region $AWS_REGION
    
    echo -e "${GREEN}✅ ECS service updated${NC}"
}

# Wait for deployment to complete
wait_for_deployment() {
    echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
    
    $AWS_CLI_PATH ecs wait services-stable \
        --cluster $PROJECT_NAME-cluster \
        --services $PROJECT_NAME-service \
        --region $AWS_REGION
    
    echo -e "${GREEN}✅ Deployment completed successfully${NC}"
}

# Run health checks
run_health_checks() {
    echo -e "${YELLOW}🏥 Running health checks...${NC}"
    
    # Get ALB DNS name
    ALB_DNS=$(cd $TERRAFORM_DIR && terraform output -raw alb_dns_name)
    
    # Wait for ALB to be ready
    echo "Waiting for Application Load Balancer to be ready..."
    sleep 60
    
    # Test health endpoint
    if curl -f "http://$ALB_DNS/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
}

# Display deployment summary
display_summary() {
    echo -e "${GREEN}🎉 Deployment Summary${NC}"
    echo "=================="
    
    ALB_DNS=$(cd $TERRAFORM_DIR && terraform output -raw alb_dns_name)
    
    echo -e "${GREEN}🌐 Application URL: http://$ALB_DNS${NC}"
    echo -e "${GREEN}📊 Grafana Dashboard: http://$ALB_DNS:3001${NC}"
    echo -e "${GREEN}📈 Prometheus Metrics: http://$ALB_DNS:9090${NC}"
    echo -e "${GREEN}🗄️ pgAdmin: http://$ALB_DNS:5050${NC}"
    echo -e "${GREEN}🐰 RabbitMQ Management: http://$ALB_DNS:15672${NC}"
    
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. Configure your domain name to point to the ALB"
    echo "2. Set up SSL certificates for HTTPS"
    echo "3. Configure monitoring alerts"
    echo "4. Set up automated backups"
    echo "5. Configure auto-scaling policies"
}

# Main deployment function
main() {
    check_prerequisites
    get_aws_account_id
    build_and_push_images
    deploy_infrastructure
    update_ecs_service
    wait_for_deployment
    run_health_checks
    display_summary
}

# Run main function
main "$@"
