# 1. The ECR Repository
resource "aws_ecr_repository" "app_repo" {
  name                 = "trading-notifications-snow-leopard"
  image_tag_mutability = "MUTABLE"             # Essential if you want to overwrite 'latest'
}

# 2. Lifecycle Policy (Cost Saver)
# This rule keeps only the last 5 images and expires untagged ones to save storage costs.
resource "aws_ecr_lifecycle_policy" "app_repo_policy" {
  repository = aws_ecr_repository.app_repo.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "latest"] # Adjust based on your tagging strategy
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Expire untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
