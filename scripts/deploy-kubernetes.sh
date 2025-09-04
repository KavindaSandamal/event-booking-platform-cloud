#!/bin/bash

# Kubernetes Deployment Script for Event Booking Platform
# This script deploys the application to EKS cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="event-booking-platform"
NAMESPACE="event-booking-platform"
AWS_REGION="us-west-2"
CLUSTER_NAME="${PROJECT_NAME}-cluster"

echo -e "${BLUE}🚀 Starting Kubernetes Deployment${NC}"
echo "================================================"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if aws CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if eksctl is installed
    if ! command -v eksctl &> /dev/null; then
        echo -e "${RED}❌ eksctl is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Configure kubectl for EKS
configure_kubectl() {
    echo -e "${YELLOW}🔧 Configuring kubectl for EKS...${NC}"
    
    # Update kubeconfig
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    # Verify connection
    if kubectl get nodes > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Successfully connected to EKS cluster${NC}"
    else
        echo -e "${RED}❌ Failed to connect to EKS cluster${NC}"
        exit 1
    fi
}

# Create namespace
create_namespace() {
    echo -e "${YELLOW}📦 Creating namespace...${NC}"
    
    kubectl apply -f infrastructure/kubernetes/namespace.yaml
    
    echo -e "${GREEN}✅ Namespace created${NC}"
}

# Deploy secrets
deploy_secrets() {
    echo -e "${YELLOW}🔐 Deploying secrets...${NC}"
    
    # Check if secrets file exists
    if [ ! -f "infrastructure/kubernetes/secrets.yaml" ]; then
        echo -e "${RED}❌ secrets.yaml not found. Please create it first.${NC}"
        exit 1
    fi
    
    kubectl apply -f infrastructure/kubernetes/secrets.yaml
    
    echo -e "${GREEN}✅ Secrets deployed${NC}"
}

# Deploy configmap
deploy_configmap() {
    echo -e "${YELLOW}⚙️ Deploying configmap...${NC}"
    
    kubectl apply -f infrastructure/kubernetes/configmap.yaml
    
    echo -e "${GREEN}✅ ConfigMap deployed${NC}"
}

# Deploy services
deploy_services() {
    echo -e "${YELLOW}🚀 Deploying services...${NC}"
    
    # Deploy all service deployments
    kubectl apply -f infrastructure/kubernetes/auth-deployment.yaml
    kubectl apply -f infrastructure/kubernetes/catalog-deployment.yaml
    kubectl apply -f infrastructure/kubernetes/booking-deployment.yaml
    kubectl apply -f infrastructure/kubernetes/payment-deployment.yaml
    kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
    kubectl apply -f infrastructure/kubernetes/worker-deployment.yaml
    
    echo -e "${GREEN}✅ Services deployed${NC}"
}

# Deploy ingress
deploy_ingress() {
    echo -e "${YELLOW}🌐 Deploying ingress...${NC}"
    
    # Install NGINX Ingress Controller if not exists
    if ! kubectl get namespace ingress-nginx > /dev/null 2>&1; then
        echo "Installing NGINX Ingress Controller..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml
        
        # Wait for ingress controller to be ready
        echo "Waiting for NGINX Ingress Controller to be ready..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
    fi
    
    # Deploy ingress
    kubectl apply -f infrastructure/kubernetes/ingress.yaml
    
    echo -e "${GREEN}✅ Ingress deployed${NC}"
}

# Deploy HPA
deploy_hpa() {
    echo -e "${YELLOW}📈 Deploying Horizontal Pod Autoscaler...${NC}"
    
    kubectl apply -f infrastructure/kubernetes/hpa.yaml
    
    echo -e "${GREEN}✅ HPA deployed${NC}"
}

# Wait for deployments
wait_for_deployments() {
    echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
    
    deployments=("auth-service" "catalog-service" "booking-service" "payment-service" "frontend-service")
    
    for deployment in "${deployments[@]}"; do
        echo "Waiting for $deployment..."
        kubectl wait --for=condition=available --timeout=300s deployment/$deployment -n $NAMESPACE
    done
    
    echo -e "${GREEN}✅ All deployments are ready${NC}"
}

# Check deployment status
check_status() {
    echo -e "${YELLOW}📊 Checking deployment status...${NC}"
    
    echo "Pods:"
    kubectl get pods -n $NAMESPACE
    
    echo ""
    echo "Services:"
    kubectl get services -n $NAMESPACE
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n $NAMESPACE
    
    echo ""
    echo "HPA:"
    kubectl get hpa -n $NAMESPACE
}

# Get application URL
get_application_url() {
    echo -e "${YELLOW}🌐 Getting application URL...${NC}"
    
    # Get ingress external IP
    EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo -e "${GREEN}🌐 Application URL: http://$EXTERNAL_IP${NC}"
        echo -e "${GREEN}📚 API Documentation: http://$EXTERNAL_IP/docs${NC}"
    else
        echo -e "${YELLOW}⚠️ External IP not available yet. Check with: kubectl get ingress -n $NAMESPACE${NC}"
    fi
}

# Run health checks
run_health_checks() {
    echo -e "${YELLOW}🏥 Running health checks...${NC}"
    
    # Get external IP
    EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        # Wait a bit for the service to be ready
        sleep 30
        
        # Test health endpoint
        if curl -f "http://$EXTERNAL_IP/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Health check passed${NC}"
        else
            echo -e "${YELLOW}⚠️ Health check failed, but deployment might still be starting${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Cannot run health checks - external IP not available${NC}"
    fi
}

# Display deployment summary
display_summary() {
    echo -e "${GREEN}🎉 Deployment Summary${NC}"
    echo "=================="
    
    EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get ingress event-booking-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo -e "${GREEN}🌐 Application URL: http://$EXTERNAL_IP${NC}"
        echo -e "${GREEN}📚 API Documentation: http://$EXTERNAL_IP/docs${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Useful Commands:${NC}"
    echo "kubectl get pods -n $NAMESPACE"
    echo "kubectl get services -n $NAMESPACE"
    echo "kubectl get ingress -n $NAMESPACE"
    echo "kubectl logs -f deployment/auth-service -n $NAMESPACE"
    echo "kubectl describe pod <pod-name> -n $NAMESPACE"
    
    echo ""
    echo -e "${YELLOW}📊 Monitoring:${NC}"
    echo "kubectl top pods -n $NAMESPACE"
    echo "kubectl get hpa -n $NAMESPACE"
}

# Main deployment function
main() {
    check_prerequisites
    configure_kubectl
    create_namespace
    deploy_secrets
    deploy_configmap
    deploy_services
    deploy_ingress
    deploy_hpa
    wait_for_deployments
    check_status
    get_application_url
    run_health_checks
    display_summary
}

# Run main function
main "$@"
