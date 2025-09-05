# Kafka Infrastructure Setup Script
# This script sets up MSK (Managed Streaming for Apache Kafka) on AWS

param(
    [string]$AwsRegion = "us-west-2",
    [string]$ClusterName = "event-booking-kafka-cluster"
)

Write-Host "Setting up Kafka Infrastructure for Scaling" -ForegroundColor Blue
Write-Host "================================================"

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Get VPC and Subnet information
Write-Host "Getting VPC and Subnet information..." -ForegroundColor Yellow

# Get default VPC
$vpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $AwsRegion
Write-Host "Using VPC: $vpcId" -ForegroundColor Green

# Get subnets
$subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[].SubnetId" --output text --region $AwsRegion
$subnetArray = $subnets -split "`t"
Write-Host "Found subnets: $($subnetArray -join ', ')" -ForegroundColor Green

# Get security groups
$securityGroupId = aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpcId" "Name=group-name,Values=default" --query "SecurityGroups[0].GroupId" --output text --region $AwsRegion
Write-Host "Using security group: $securityGroupId" -ForegroundColor Green

# Create MSK cluster
Write-Host "Creating MSK Kafka cluster..." -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes. Please wait..." -ForegroundColor Cyan

# MSK cluster configuration
$mskConfig = @{
    "cluster_name" = $ClusterName
    "kafka_version" = "2.8.1"
    "number_of_broker_nodes" = 3
    "broker_node_group_info" = @{
        "instance_type" = "kafka.t3.small"
        "client_subnets" = $subnetArray
        "security_groups" = @($securityGroupId)
        "storage_info" = @{
            "ebs_storage_info" = @{
                "volume_size" = 20
            }
        }
    }
    "encryption_info" = @{
        "encryption_in_transit" = @{
            "client_broker" = "TLS"
        }
    }
    "client_authentication" = @{
        "sasl" = @{
            "scram" = @{
                "enabled" = $true
            }
        }
    }
}

# Convert to JSON
$mskConfigJson = $mskConfig | ConvertTo-Json -Depth 10

# Save config to file
$mskConfigJson | Out-File -FilePath "msk-cluster-config.json" -Encoding UTF8

Write-Host "MSK cluster configuration saved to msk-cluster-config.json" -ForegroundColor Green
Write-Host "To create the cluster, run:" -ForegroundColor Cyan
Write-Host "aws kafka create-cluster --cli-input-json file://msk-cluster-config.json --region $AwsRegion" -ForegroundColor Cyan

Write-Host "`nAlternative: Use AWS Console" -ForegroundColor Yellow
Write-Host "1. Go to Amazon MSK in AWS Console" -ForegroundColor Cyan
Write-Host "2. Create cluster with these settings:" -ForegroundColor Cyan
Write-Host "   - Cluster name: $ClusterName" -ForegroundColor Cyan
Write-Host "   - Kafka version: 2.8.1" -ForegroundColor Cyan
Write-Host "   - Broker nodes: 3" -ForegroundColor Cyan
Write-Host "   - Instance type: kafka.t3.small" -ForegroundColor Cyan
Write-Host "   - Storage: 20 GB EBS per broker" -ForegroundColor Cyan

Write-Host "`nAfter cluster is created, update the task definition with the cluster endpoint." -ForegroundColor Yellow
Write-Host "The cluster endpoint will be: $ClusterName.kafka.$AwsRegion.amazonaws.com:9092" -ForegroundColor Green
