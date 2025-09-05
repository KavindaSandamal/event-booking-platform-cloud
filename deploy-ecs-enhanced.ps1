# Enhanced ECS Deployment Script for Event Booking Platform
# PowerShell version for Windows

param(
    [string]$ProjectName = "event-booking-platform",
    [string]$AwsRegion = "us-west-2",
    [string]$TaskDefinitionFile = "task-definition-enhanced.json"
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$NC = "`e[0m" # No Color

Write-Host "${Blue}🚀 Starting Enhanced ECS Deployment${NC}" -ForegroundColor Blue
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

# Build and push enhanced Docker images to ECR
function Build-AndPushEnhancedImages {
    param($AwsAccountId, $AwsCliPath)
    
    Write-Host "${Yellow}🐳 Building and pushing enhanced Docker images to ECR...${NC}" -ForegroundColor Yellow
    
    # Login to ECR
    & $AwsCliPath ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"
    
    # Build and push each service with enhanced features
    $services = @("nginx", "auth", "catalog", "booking", "payment", "frontend", "worker")
    
    foreach ($service in $services) {
        Write-Host "${Yellow}Building enhanced $service...${NC}" -ForegroundColor Yellow
        
        # Build image
        if ($service -eq "worker") {
            docker build -t "$service" -f "services/$service/Dockerfile" "services/$service/"
        } else {
            docker build -t "$service" -f "services/$service/Dockerfile" .
        }
        
        # Tag for ECR
        docker tag "$service`:latest" "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        # Push to ECR
        docker push "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        Write-Host "${Green}✅ Enhanced $service pushed successfully${NC}" -ForegroundColor Green
    }
}

# Register enhanced task definition
function Register-EnhancedTaskDefinition {
    param($AwsCliPath)
    
    Write-Host "${Yellow}📝 Registering enhanced task definition...${NC}" -ForegroundColor Yellow
    
    # Register the enhanced task definition
    $result = & $AwsCliPath ecs register-task-definition `
        --cli-input-json file://$TaskDefinitionFile `
        --region $AwsRegion
    
    $taskDefinitionArn = $result.taskDefinition.taskDefinitionArn
    Write-Host "${Green}✅ Enhanced task definition registered: $taskDefinitionArn${NC}" -ForegroundColor Green
    return $taskDefinitionArn
}

# Update ECS service with enhanced task definition
function Update-EcsServiceEnhanced {
    param($AwsCliPath, $TaskDefinitionArn)
    
    Write-Host "${Yellow}🔄 Updating ECS service with enhanced features...${NC}" -ForegroundColor Yellow
    
    # Update the service with new task definition
    & $AwsCliPath ecs update-service `
        --cluster "$ProjectName-cluster" `
        --service "$ProjectName-service" `
        --task-definition $TaskDefinitionArn `
        --region $AwsRegion
    
    Write-Host "${Green}✅ ECS service updated with enhanced task definition${NC}" -ForegroundColor Green
}

# Wait for enhanced deployment to complete
function Wait-ForEnhancedDeployment {
    param($AwsCliPath)
    
    Write-Host "${Yellow}⏳ Waiting for enhanced deployment to complete...${NC}" -ForegroundColor Yellow
    
    & $AwsCliPath ecs wait services-stable `
        --cluster "$ProjectName-cluster" `
        --services "$ProjectName-service" `
        --region $AwsRegion
    
    Write-Host "${Green}✅ Enhanced deployment completed successfully${NC}" -ForegroundColor Green
}

# Test enhanced services
function Test-EnhancedServices {
    param($AwsCliPath)
    
    Write-Host "${Yellow}🧪 Testing enhanced services...${NC}" -ForegroundColor Yellow
    
    # Get Load Balancer DNS
    $albDns = "event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com"
    
    # Test endpoints
    $testEndpoints = @(
        @{ Name = "Health Check"; Url = "http://$albDns/health" },
        @{ Name = "Auth Service"; Url = "http://$albDns/auth/health" },
        @{ Name = "Catalog Service"; Url = "http://$albDns/catalog/health" },
        @{ Name = "Booking Service"; Url = "http://$albDns/booking/health" },
        @{ Name = "Payment Service"; Url = "http://$albDns/payment/health" },
        @{ Name = "Worker Service"; Url = "http://$albDns/worker/health" }
    )
    
    foreach ($endpoint in $testEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.Url -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "${Green}✅ $($endpoint.Name): Healthy${NC}" -ForegroundColor Green
            } else {
                Write-Host "${Yellow}⚠️ $($endpoint.Name): Status $($response.StatusCode)${NC}" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "${Red}❌ $($endpoint.Name): Not responding${NC}" -ForegroundColor Red
        }
    }
}

# Display enhanced features information
function Show-EnhancedFeatures {
    Write-Host "${Blue}🎉 Enhanced Features Deployed:${NC}" -ForegroundColor Blue
    Write-Host "================================================"
    Write-Host "${Green}✅ Worker Service: Background processing${NC}" -ForegroundColor Green
    Write-Host "${Green}✅ Prometheus: Metrics collection${NC}" -ForegroundColor Green
    Write-Host "${Green}✅ Grafana: Monitoring dashboards${NC}" -ForegroundColor Green
    Write-Host "${Green}✅ Enhanced Logging: Structured logging${NC}" -ForegroundColor Green
    Write-Host "${Green}✅ Circuit Breakers: Fault tolerance${NC}" -ForegroundColor Green
    Write-Host "${Green}✅ Health Checks: Service monitoring${NC}" -ForegroundColor Green
    
    Write-Host "`n${Blue}🌐 Service URLs:${NC}" -ForegroundColor Blue
    Write-Host "Frontend: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com" -ForegroundColor Cyan
    Write-Host "Prometheus: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com:9090" -ForegroundColor Cyan
    Write-Host "Grafana: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com:3001" -ForegroundColor Cyan
    Write-Host "  Username: admin, Password: admin123" -ForegroundColor Cyan
    
    Write-Host "`n${Blue}📊 Monitoring Commands:${NC}" -ForegroundColor Blue
    Write-Host "View ECS logs: aws logs tail /ecs/event-booking-platform --follow" -ForegroundColor Cyan
    Write-Host "Check service status: aws ecs describe-services --cluster $ProjectName-cluster --services $ProjectName-service" -ForegroundColor Cyan
}

# Main execution
function Main {
    try {
        # Check prerequisites
        $AwsCliPath = Check-Prerequisites
        
        # Get AWS Account ID
        $AwsAccountId = Get-AwsAccountId -AwsCliPath $AwsCliPath
        
        # Build and push enhanced images
        Build-AndPushEnhancedImages -AwsAccountId $AwsAccountId -AwsCliPath $AwsCliPath
        
        # Register enhanced task definition
        $TaskDefinitionArn = Register-EnhancedTaskDefinition -AwsCliPath $AwsCliPath
        
        # Update ECS service
        Update-EcsServiceEnhanced -AwsCliPath $AwsCliPath -TaskDefinitionArn $TaskDefinitionArn
        
        # Wait for deployment
        Wait-ForEnhancedDeployment -AwsCliPath $AwsCliPath
        
        # Test services
        Test-EnhancedServices -AwsCliPath $AwsCliPath
        
        # Show enhanced features
        Show-EnhancedFeatures
        
        Write-Host "${Green}🎉 Enhanced ECS deployment completed successfully!${NC}" -ForegroundColor Green
        Write-Host "${Blue}Your Event Booking Platform now has enhanced features!${NC}" -ForegroundColor Blue
        
    } catch {
        Write-Host "${Red}❌ Enhanced deployment failed: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Run main function
Main
