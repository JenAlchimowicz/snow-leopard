# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "trading-notifications-cluster"
}

# CloudWatch Log Group for ECS tasks
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/trading-notifications"
  retention_in_days = 30
}

# ECS Task Execution Role (needed by ECS to pull image and write logs)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "trading-notifications-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (permissions your container code needs at runtime)
resource "aws_iam_role" "ecs_task_role" {
  name = "trading-notifications-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Task role policy for S3, Secrets Manager, and SES access
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "ecs-task-permissions"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.trading-notifications-s3-bucket.arn,
          "${aws_s3_bucket.trading-notifications-s3-bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.trading-notifications-secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "trading_notifications" {
  family                   = "trading-notifications"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"  # 2 vCPU
  memory                   = "8192"  # 8 GB
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "trading-notifications"
      image     = "${aws_ecr_repository.app_repo.repository_url}:latest"
      essential = true

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "eu-west-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      # Environment variables
      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = "eu-west-1"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.trading-notifications-s3-bucket.bucket
        }
      ]
    }
  ])
}

# VPC and networking (required for Fargate)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for ECS task
resource "aws_security_group" "ecs_task" {
  name        = "trading-notifications-ecs-task"
  description = "Security group for trading notifications ECS task"
  vpc_id      = data.aws_vpc.default.id

  # Allow all outbound traffic (needed for pulling Docker images, accessing AWS services)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EventBridge Scheduler IAM Role
resource "aws_iam_role" "eventbridge_scheduler_role" {
  name = "trading-notifications-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_scheduler_policy" {
  name = "eventbridge-ecs-run-task"
  role = aws_iam_role.eventbridge_scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = aws_ecs_task_definition.trading_notifications.arn
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      }
    ]
  })
}

# EventBridge Scheduler
resource "aws_scheduler_schedule" "daily_task" {
  name       = "trading-notifications-daily"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 22 * * ? *)"

  schedule_expression_timezone = "Europe/London"

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.eventbridge_scheduler_role.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.trading_notifications.arn
      launch_type         = "FARGATE"

      network_configuration {
        subnets          = data.aws_subnets.default.ids
        security_groups  = [aws_security_group.ecs_task.id]
        assign_public_ip = true  # Required for pulling images from ECR
      }
    }

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}

# Outputs for reference
output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_task_definition" {
  value = aws_ecs_task_definition.trading_notifications.family
}

output "scheduler_name" {
  value = aws_scheduler_schedule.daily_task.name
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.ecs_logs.name
}