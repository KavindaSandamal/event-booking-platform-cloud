output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.main.name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "mq_endpoint" {
  description = "Amazon MQ endpoint"
  value       = aws_mq_broker.main.instances[0].endpoints[0]
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    nginx    = aws_ecr_repository.nginx.repository_url
    auth     = aws_ecr_repository.auth.repository_url
    catalog  = aws_ecr_repository.catalog.repository_url
    booking  = aws_ecr_repository.booking.repository_url
    payment  = aws_ecr_repository.payment.repository_url
    frontend = aws_ecr_repository.frontend.repository_url
  }
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.main.name
}
