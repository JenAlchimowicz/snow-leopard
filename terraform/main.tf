terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_s3_bucket" "trading-notifications-s3-bucket" {
  bucket = "trading-notifications-snow-leopard-1"
}

resource "aws_secretsmanager_secret" "trading-notifications-secrets" {
  name        = "trading-notifications-secrets"
  description = "Stores eodhd api key and app configuration"
}
