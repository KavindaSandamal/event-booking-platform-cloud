variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "event-booking-platform"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "task_cpu" {
  description = "CPU units for ECS task"
  type        = string
  default     = "1024"
}

variable "task_memory" {
  description = "Memory for ECS task"
  type        = string
  default     = "2048"
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
}

variable "db_instance_class" {
  description = "RDS instance class (Free Tier: db.t3.micro)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "eventdb"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type (Free Tier: cache.t3.micro)"
  type        = string
  default     = "cache.t3.micro"
}

variable "mq_instance_type" {
  description = "Amazon MQ instance type (Free Tier: mq.t3.micro)"
  type        = string
  default     = "mq.t3.micro"
}

variable "eks_node_instance_type" {
  description = "EKS node instance type (Free Tier: t3.micro)"
  type        = string
  default     = "t3.micro"
}

variable "eks_node_desired_size" {
  description = "Desired number of EKS nodes (Free Tier: 2)"
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "Maximum number of EKS nodes (Free Tier: 4)"
  type        = number
  default     = 4
}

variable "eks_node_min_size" {
  description = "Minimum number of EKS nodes (Free Tier: 1)"
  type        = number
  default     = 1
}

variable "mq_password" {
  description = "Amazon MQ password"
  type        = string
  sensitive   = true
}
