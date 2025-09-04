# AWS Cloud-Native Deployment Script for Event Booking Platform
# Simple PowerShell version

param(
    [string]$ProjectName = "event-booking-platform",
    [string]$AwsRegion = "us-west-2"
)

Write-Host "🚀 Starting AWS Cloud-Native Deployment" -ForegroundColor Blue
Write-Host "================================================"

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check Terraform
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Terraform is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials configured" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites met" -ForegroundColor Green

# Get AWS Account ID
Write-Host "🔍 Getting AWS Account ID..." -ForegroundColor Yellow
$AwsAccountId = aws sts get-caller-identity --query Account --output text
Write-Host "✅ AWS Account ID: $AwsAccountId" -ForegroundColor Green

# Deploy infrastructure with Terraform
Write-Host "🏗️ Deploying infrastructure with Terraform..." -ForegroundColor Yellow
Set-Location "infrastructure/aws/terraform"

try {
    # Initialize Terraform
    Write-Host "Initializing Terraform..." -ForegroundColor Yellow
    terraform init
    
    # Apply Terraform configuration
    Write-Host "Applying Terraform configuration..." -ForegroundColor Yellow
    terraform apply -var="aws_account_id=$AwsAccountId" -var="aws_region=$AwsRegion" -var="mq_password=7ENBh1tJ@05h.;W[" -var="db_password=H_r4Q7wZs0YS" -auto-approve
    
    Write-Host "✅ Infrastructure deployed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Infrastructure deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Set-Location "../../.."
}

# Build and push Docker images to ECR
Write-Host "🐳 Building and pushing Docker images to ECR..." -ForegroundColor Yellow

# Login to ECR
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"

# Build and push each service
$services = @("nginx", "auth", "catalog", "booking", "payment", "frontend")

foreach ($service in $services) {
    Write-Host "Building $service..." -ForegroundColor Yellow
    
    # Build image from the service directory
    $servicePath = Join-Path "services" $service
    if (Test-Path $servicePath) {
        Push-Location $servicePath
        docker build -t "$service" .
        Pop-Location
        
        # Tag for ECR
        docker tag "$service`:latest" "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        # Push to ECR
        docker push "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        Write-Host "✅ $service pushed successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Skipping $service - directory not found" -ForegroundColor Yellow
    }
}

# Update ECS service
Write-Host "🔄 Updating ECS service..." -ForegroundColor Yellow
aws ecs update-service --cluster "$ProjectName-cluster" --service "$ProjectName-service" --force-new-deployment --region $AwsRegion

# Wait for deployment to complete
Write-Host "⏳ Waiting for deployment to complete..." -ForegroundColor Yellow
aws ecs wait services-stable --cluster "$ProjectName-cluster" --services "$ProjectName-service" --region $AwsRegion

Write-Host "✅ Deployment completed successfully" -ForegroundColor Green

# Get deployment information
Write-Host "📊 Getting deployment information..." -ForegroundColor Yellow

# Get Load Balancer DNS
$albDns = terraform -chdir="infrastructure/aws/terraform" output -raw alb_dns_name
Write-Host "🌐 Application URL: http://$albDns" -ForegroundColor Green

# Get ECR repositories
$ecrRepos = terraform -chdir="infrastructure/aws/terraform" output -json ecr_repositories | ConvertFrom-Json
Write-Host "📦 ECR Repositories:" -ForegroundColor Green
foreach ($repo in $ecrRepos.PSObject.Properties) {
    Write-Host "  - $($repo.Name): $($repo.Value)" -ForegroundColor Green
}

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "Your Event Booking Platform is now running on AWS!" -ForegroundColor Blue
