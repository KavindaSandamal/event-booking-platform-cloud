# AWS Cloud-Native Deployment Script for Event Booking Platform
# PowerShell version for Windows

param(
    [string]$ProjectName = "event-booking-platform",
    [string]$AwsRegion = "us-west-2",
    [string]$TerraformDir = "infrastructure/aws/terraform"
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$NC = "`e[0m" # No Color

Write-Host "${Blue}🚀 Starting AWS Cloud-Native Deployment${NC}" -ForegroundColor Blue
Write-Host "================================================"

# Check prerequisites
function Check-Prerequisites {
    Write-Host "${Yellow}📋 Checking prerequisites...${NC}" -ForegroundColor Yellow
    
    # Check if AWS CLI is installed
    $AwsCliPath = ""
    if (Get-Command aws -ErrorAction SilentlyContinue) {
        $AwsCliPath = "aws"
    } elseif (Test-Path "C:\Program Files\Amazon\AWSCLIV2\aws.exe") {
        $AwsCliPath = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
    } else {
        Write-Host "${Red}❌ AWS CLI is not installed. Please install it first.${NC}" -ForegroundColor Red
        exit 1
    }
    
    # Check if Terraform is installed
    if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
        Write-Host "${Red}❌ Terraform is not installed. Please install it first.${NC}" -ForegroundColor Red
        exit 1
    }
    
    # Check if Docker is installed
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "${Red}❌ Docker is not installed. Please install it first.${NC}" -ForegroundColor Red
        exit 1
    }
    
    # Check AWS credentials
    try {
        & $AwsCliPath sts get-caller-identity | Out-Null
    } catch {
        Write-Host "${Red}❌ AWS credentials not configured. Please run 'aws configure' first.${NC}" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "${Green}✅ All prerequisites met${NC}" -ForegroundColor Green
    return $AwsCliPath
}

# Get AWS Account ID
function Get-AwsAccountId {
    param($AwsCliPath)
    
    Write-Host "${Yellow}🔍 Getting AWS Account ID...${NC}" -ForegroundColor Yellow
    $AwsAccountId = & $AwsCliPath sts get-caller-identity --query Account --output text
    Write-Host "${Green}✅ AWS Account ID: $AwsAccountId${NC}" -ForegroundColor Green
    return $AwsAccountId
}

# Build and push Docker images to ECR
function Build-AndPushImages {
    param($AwsAccountId, $AwsCliPath)
    
    Write-Host "${Yellow}🐳 Building and pushing Docker images to ECR...${NC}" -ForegroundColor Yellow
    
    # Login to ECR
    & $AwsCliPath ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"
    
    # Build and push each service
    $services = @("nginx", "auth", "catalog", "booking", "payment", "frontend")
    
    foreach ($service in $services) {
        Write-Host "${Yellow}Building $service...${NC}" -ForegroundColor Yellow
        
        # Build image
        docker build -t "$service" -f "services/$service/Dockerfile" .
        
        # Tag for ECR
        docker tag "$service`:latest" "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        # Push to ECR
        docker push "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        Write-Host "${Green}✅ $service pushed successfully${NC}" -ForegroundColor Green
    }
}

# Deploy infrastructure with Terraform
function Deploy-Infrastructure {
    param($AwsAccountId)
    
    Write-Host "${Yellow}🏗️ Deploying infrastructure with Terraform...${NC}" -ForegroundColor Yellow
    
    Push-Location $TerraformDir
    
    try {
        # Initialize Terraform
        Write-Host "${Yellow}Initializing Terraform...${NC}" -ForegroundColor Yellow
        terraform init
        
        # Apply Terraform configuration
        Write-Host "${Yellow}Applying Terraform configuration...${NC}" -ForegroundColor Yellow
        terraform apply -var="aws_account_id=$AwsAccountId" -var="aws_region=$AwsRegion" -var="mq_password=7ENBh1tJ@05h.;W[" -var="db_password=H_r4/Q7=wZ:s0Y/S" -auto-approve
        
        Write-Host "${Green}✅ Infrastructure deployed successfully${NC}" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# Update ECS service
function Update-EcsService {
    param($AwsCliPath)
    
    Write-Host "${Yellow}🔄 Updating ECS service...${NC}" -ForegroundColor Yellow
    
    # Force new deployment
    & $AwsCliPath ecs update-service `
        --cluster "$ProjectName-cluster" `
        --service "$ProjectName-service" `
        --force-new-deployment `
        --region $AwsRegion
}

# Wait for deployment to complete
function Wait-ForDeployment {
    param($AwsCliPath)
    
    Write-Host "${Yellow}⏳ Waiting for deployment to complete...${NC}" -ForegroundColor Yellow
    
    & $AwsCliPath ecs wait services-stable `
        --cluster "$ProjectName-cluster" `
        --services "$ProjectName-service" `
        --region $AwsRegion
    
    Write-Host "${Green}✅ Deployment completed successfully${NC}" -ForegroundColor Green
}

# Get deployment information
function Get-DeploymentInfo {
    param($AwsCliPath)
    
    Write-Host "${Yellow}📊 Getting deployment information...${NC}" -ForegroundColor Yellow
    
    # Get Load Balancer DNS
    $albDns = terraform -chdir=$TerraformDir output -raw alb_dns_name
    Write-Host "${Green}🌐 Application URL: http://$albDns${NC}" -ForegroundColor Green
    
    # Get ECR repositories
    $ecrRepos = terraform -chdir=$TerraformDir output -json ecr_repositories | ConvertFrom-Json
    Write-Host "${Green}📦 ECR Repositories:${NC}" -ForegroundColor Green
    foreach ($repo in $ecrRepos.PSObject.Properties) {
        Write-Host "  - $($repo.Name): $($repo.Value)" -ForegroundColor Green
    }
}

# Main execution
function Main {
    try {
        # Check prerequisites
        $AwsCliPath = Check-Prerequisites
        
        # Get AWS Account ID
        $AwsAccountId = Get-AwsAccountId -AwsCliPath $AwsCliPath
        
        # Deploy infrastructure
        Deploy-Infrastructure -AwsAccountId $AwsAccountId
        
        # Build and push images
        Build-AndPushImages -AwsAccountId $AwsAccountId -AwsCliPath $AwsCliPath
        
        # Update ECS service
        Update-EcsService -AwsCliPath $AwsCliPath
        
        # Wait for deployment
        Wait-ForDeployment -AwsCliPath $AwsCliPath
        
        # Get deployment info
        Get-DeploymentInfo -AwsCliPath $AwsCliPath
        
        Write-Host "${Green}🎉 Deployment completed successfully!${NC}" -ForegroundColor Green
        Write-Host "${Blue}Your Event Booking Platform is now running on AWS!${NC}" -ForegroundColor Blue
        
    } catch {
        Write-Host "${Red}❌ Deployment failed: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Run main function
Main
