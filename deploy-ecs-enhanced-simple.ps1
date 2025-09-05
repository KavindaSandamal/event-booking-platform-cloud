# Enhanced ECS Deployment Script for Event Booking Platform
# PowerShell version for Windows

param(
    [string]$ProjectName = "event-booking-platform",
    [string]$AwsRegion = "us-west-2",
    [string]$TaskDefinitionFile = "task-definition-enhanced.json"
)

Write-Host "Starting Enhanced ECS Deployment" -ForegroundColor Blue
Write-Host "================================================"

# Check prerequisites
function Check-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check if AWS CLI is installed
    $AwsCliPath = ""
    if (Get-Command aws -ErrorAction SilentlyContinue) {
        $AwsCliPath = "aws"
    } elseif (Test-Path "C:\Program Files\Amazon\AWSCLIV2\aws.exe") {
        $AwsCliPath = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
    } else {
        Write-Host "AWS CLI is not installed. Please install it first." -ForegroundColor Red
        exit 1
    }
    
    # Check if Docker is installed
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "Docker is not installed. Please install it first." -ForegroundColor Red
        exit 1
    }
    
    # Check AWS credentials
    try {
        & $AwsCliPath sts get-caller-identity | Out-Null
    } catch {
        Write-Host "AWS credentials not configured. Please run 'aws configure' first." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "All prerequisites met" -ForegroundColor Green
    return $AwsCliPath
}

# Get AWS Account ID
function Get-AwsAccountId {
    param($AwsCliPath)
    
    Write-Host "Getting AWS Account ID..." -ForegroundColor Yellow
    $AwsAccountId = & $AwsCliPath sts get-caller-identity --query Account --output text
    Write-Host "AWS Account ID: $AwsAccountId" -ForegroundColor Green
    return $AwsAccountId
}

# Build and push enhanced Docker images to ECR
function Build-AndPushEnhancedImages {
    param($AwsAccountId, $AwsCliPath)
    
    Write-Host "Building and pushing enhanced Docker images to ECR..." -ForegroundColor Yellow
    
    # Login to ECR
    & $AwsCliPath ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"
    
    # Build and push each service with enhanced features
    $services = @("nginx", "auth", "catalog", "booking", "payment", "frontend", "worker")
    
    foreach ($service in $services) {
        Write-Host "Building enhanced $service..." -ForegroundColor Yellow
        
        # Build image
        if ($service -eq "worker") {
            docker build -t "$service" -f "services/$service/Dockerfile" "services/$service/"
        } else {
            docker build -t "$service" -f "services/$service/Dockerfile" "services/$service/"
        }
        
        # Tag for ECR
        docker tag "$service`:latest" "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        # Push to ECR
        docker push "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/$ProjectName-$service`:latest"
        
        Write-Host "Enhanced $service pushed successfully" -ForegroundColor Green
    }
}

# Register enhanced task definition
function Register-EnhancedTaskDefinition {
    param($AwsCliPath)
    
    Write-Host "Registering enhanced task definition..." -ForegroundColor Yellow
    
    # Register the enhanced task definition
    $result = & $AwsCliPath ecs register-task-definition `
        --cli-input-json file://$TaskDefinitionFile `
        --region $AwsRegion
    
    $taskDefinitionArn = $result.taskDefinition.taskDefinitionArn
    Write-Host "Enhanced task definition registered: $taskDefinitionArn" -ForegroundColor Green
    return $taskDefinitionArn
}

# Update ECS service with enhanced task definition
function Update-EcsServiceEnhanced {
    param($AwsCliPath, $TaskDefinitionArn)
    
    Write-Host "Updating ECS service with enhanced features..." -ForegroundColor Yellow
    
    # Update the service with new task definition
    & $AwsCliPath ecs update-service `
        --cluster "$ProjectName-cluster" `
        --service "$ProjectName-service" `
        --task-definition $TaskDefinitionArn `
        --region $AwsRegion
    
    Write-Host "ECS service updated with enhanced task definition" -ForegroundColor Green
}

# Wait for enhanced deployment to complete
function Wait-ForEnhancedDeployment {
    param($AwsCliPath)
    
    Write-Host "Waiting for enhanced deployment to complete..." -ForegroundColor Yellow
    
    & $AwsCliPath ecs wait services-stable `
        --cluster "$ProjectName-cluster" `
        --services "$ProjectName-service" `
        --region $AwsRegion
    
    Write-Host "Enhanced deployment completed successfully" -ForegroundColor Green
}

# Test enhanced services
function Test-EnhancedServices {
    param($AwsCliPath)
    
    Write-Host "Testing enhanced services..." -ForegroundColor Yellow
    
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
                Write-Host "$($endpoint.Name): Healthy" -ForegroundColor Green
            } else {
                Write-Host "$($endpoint.Name): Status $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "$($endpoint.Name): Not responding" -ForegroundColor Red
        }
    }
}

# Display enhanced features information
function Show-EnhancedFeatures {
    Write-Host "Enhanced Features Deployed:" -ForegroundColor Blue
    Write-Host "================================================"
    Write-Host "Worker Service: Background processing" -ForegroundColor Green
    Write-Host "Prometheus: Metrics collection" -ForegroundColor Green
    Write-Host "Grafana: Monitoring dashboards" -ForegroundColor Green
    Write-Host "Enhanced Logging: Structured logging" -ForegroundColor Green
    Write-Host "Circuit Breakers: Fault tolerance" -ForegroundColor Green
    Write-Host "Health Checks: Service monitoring" -ForegroundColor Green
    
    Write-Host "`nService URLs:" -ForegroundColor Blue
    Write-Host "Frontend: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com" -ForegroundColor Cyan
    Write-Host "Prometheus: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com:9090" -ForegroundColor Cyan
    Write-Host "Grafana: http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com:3001" -ForegroundColor Cyan
    Write-Host "  Username: admin, Password: admin123" -ForegroundColor Cyan
    
    Write-Host "`nMonitoring Commands:" -ForegroundColor Blue
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
        
        Write-Host "Enhanced ECS deployment completed successfully!" -ForegroundColor Green
        Write-Host "Your Event Booking Platform now has enhanced features!" -ForegroundColor Blue
        
    } catch {
        Write-Host "Enhanced deployment failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Run main function
Main
