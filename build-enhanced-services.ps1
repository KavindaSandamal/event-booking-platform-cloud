#!/usr/bin/env pwsh

param(
    [string]$AwsAccountId = "376129882286",
    [string]$AwsRegion = "us-west-2",
    [string]$ProjectName = "event-booking-platform"
)

$ECR_REGISTRY = "${AwsAccountId}.dkr.ecr.${AwsRegion}.amazonaws.com"

Write-Host "🔧 Building Enhanced Services..." -ForegroundColor Green

# Login to ECR
Write-Host "🔐 Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push Payment Service (Enhanced)
Write-Host "💳 Building Payment Service (Enhanced)..." -ForegroundColor Yellow
Set-Location "services/payment"
docker build -t "${ECR_REGISTRY}/${ProjectName}-payment:enhanced" .
docker push "${ECR_REGISTRY}/${ProjectName}-payment:enhanced"
Set-Location "../.."

# Build and push Booking Service (Enhanced)
Write-Host "📅 Building Booking Service (Enhanced)..." -ForegroundColor Yellow
Set-Location "services/booking"
docker build -t "${ECR_REGISTRY}/${ProjectName}-booking:enhanced" .
docker push "${ECR_REGISTRY}/${ProjectName}-booking:enhanced"
Set-Location "../.."

Write-Host "✅ Enhanced services built and pushed successfully!" -ForegroundColor Green
Write-Host "📦 Images available:" -ForegroundColor Cyan
Write-Host "  - ${ECR_REGISTRY}/${ProjectName}-payment:enhanced" -ForegroundColor White
Write-Host "  - ${ECR_REGISTRY}/${ProjectName}-booking:enhanced" -ForegroundColor White
