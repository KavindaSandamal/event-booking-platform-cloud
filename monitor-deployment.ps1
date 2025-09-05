# Monitor Kafka Cluster and Service Deployment
# PowerShell script to track deployment progress

param(
    [string]$AwsRegion = "us-west-2",
    [string]$ClusterArn = "arn:aws:kafka:us-west-2:376129882286:cluster/event-booking-kafka-cluster/8bf9d706-2c1c-45cb-9b9c-378aa68d3ce9-7",
    [string]$EcsCluster = "event-booking-platform-cluster",
    [string]$EcsService = "event-booking-platform-service"
)

Write-Host "Monitoring Kafka Cluster and ECS Service Deployment" -ForegroundColor Blue
Write-Host "================================================"

function Check-KafkaCluster {
    Write-Host "`nChecking Kafka Cluster Status..." -ForegroundColor Yellow
    try {
        $kafkaStatus = aws kafka describe-cluster --cluster-arn $ClusterArn --region $AwsRegion --query "ClusterInfo.State" --output text
        Write-Host "Kafka Cluster Status: $kafkaStatus" -ForegroundColor $(if ($kafkaStatus -eq "ACTIVE") { "Green" } else { "Yellow" })
        
        if ($kafkaStatus -eq "ACTIVE") {
            # Get bootstrap servers
            $bootstrapServers = aws kafka get-bootstrap-brokers --cluster-arn $ClusterArn --region $AwsRegion --query "BootstrapBrokerString" --output text
            Write-Host "Bootstrap Servers: $bootstrapServers" -ForegroundColor Green
            return $true
        }
        return $false
    } catch {
        Write-Host "Error checking Kafka cluster: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Check-EcsService {
    Write-Host "`nChecking ECS Service Status..." -ForegroundColor Yellow
    try {
        $serviceInfo = aws ecs describe-services --cluster $EcsCluster --services $EcsService --region $AwsRegion --query "services[0]" --output json | ConvertFrom-Json
        
        Write-Host "Service Status: $($serviceInfo.status)" -ForegroundColor Green
        Write-Host "Running Count: $($serviceInfo.runningCount)" -ForegroundColor Green
        Write-Host "Desired Count: $($serviceInfo.desiredCount)" -ForegroundColor Green
        Write-Host "Pending Count: $($serviceInfo.pendingCount)" -ForegroundColor Green
        
        # Check deployment status
        $deployments = $serviceInfo.deployments | Sort-Object createdAt -Descending
        $latestDeployment = $deployments[0]
        Write-Host "Latest Deployment Status: $($latestDeployment.status)" -ForegroundColor Green
        Write-Host "Deployment Created: $($latestDeployment.createdAt)" -ForegroundColor Cyan
        
        return ($serviceInfo.runningCount -eq $serviceInfo.desiredCount -and $serviceInfo.pendingCount -eq 0)
    } catch {
        Write-Host "Error checking ECS service: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-ServiceEndpoints {
    Write-Host "`nTesting Service Endpoints..." -ForegroundColor Yellow
    $albDns = "event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com"
    $testEndpoints = @(
        @{ Name = "Health Check"; Url = "http://$albDns/health" },
        @{ Name = "Auth Service"; Url = "http://$albDns/auth/health" },
        @{ Name = "Catalog Service"; Url = "http://$albDns/catalog/health" },
        @{ Name = "Booking Service"; Url = "http://$albDns/booking/health" },
        @{ Name = "Payment Service"; Url = "http://$albDns/payment/health" },
        @{ Name = "Worker Service"; Url = "http://$albDns/worker/health" }
    )
    
    $healthyCount = 0
    foreach ($endpoint in $testEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "$($endpoint.Name): Healthy" -ForegroundColor Green
                $healthyCount++
            } else {
                Write-Host "$($endpoint.Name): Status $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "$($endpoint.Name): Not responding" -ForegroundColor Red
        }
    }
    
    Write-Host "Healthy Services: $healthyCount/$($testEndpoints.Count)" -ForegroundColor $(if ($healthyCount -eq $testEndpoints.Count) { "Green" } else { "Yellow" })
    return ($healthyCount -eq $testEndpoints.Count)
}

function Show-DeploymentSummary {
    Write-Host "`nDeployment Summary:" -ForegroundColor Blue
    Write-Host "==================" -ForegroundColor Blue
    Write-Host "Kafka Cluster: Creating (takes 10-15 minutes)" -ForegroundColor Yellow
    Write-Host "ECS Services: Deploying with Kafka support" -ForegroundColor Yellow
    Write-Host "Hybrid Messaging: RabbitMQ + Kafka (when ready)" -ForegroundColor Green
    Write-Host "Scaling Features: Multiple workers, event streaming" -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Wait for Kafka cluster to become ACTIVE" -ForegroundColor Cyan
    Write-Host "2. Update task definition with Kafka endpoint" -ForegroundColor Cyan
    Write-Host "3. Deploy final version with full Kafka integration" -ForegroundColor Cyan
    
    Write-Host "`nMonitoring Commands:" -ForegroundColor Cyan
    Write-Host "Check Kafka: aws kafka describe-cluster --cluster-arn $ClusterArn --region $AwsRegion" -ForegroundColor Cyan
    Write-Host "Check ECS: aws ecs describe-services --cluster $EcsCluster --services $EcsService --region $AwsRegion" -ForegroundColor Cyan
    Write-Host "View Logs: aws logs tail /ecs/event-booking-platform --follow" -ForegroundColor Cyan
}

# Main monitoring loop
Write-Host "Starting deployment monitoring..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Cyan

$kafkaReady = $false
$servicesReady = $false
$endpointsReady = $false

while (-not ($kafkaReady -and $servicesReady -and $endpointsReady)) {
    Clear-Host
    Write-Host "Kafka-Enhanced Deployment Monitor" -ForegroundColor Blue
    Write-Host "=================================" -ForegroundColor Blue
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    
    $kafkaReady = Check-KafkaCluster
    $servicesReady = Check-EcsService
    $endpointsReady = Test-ServiceEndpoints
    
    if (-not ($kafkaReady -and $servicesReady -and $endpointsReady)) {
        Write-Host "`nWaiting 30 seconds before next check..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    }
}

Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "All services are healthy and Kafka is ready!" -ForegroundColor Green
Show-DeploymentSummary
