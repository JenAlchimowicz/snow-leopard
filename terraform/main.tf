resource "aws_s3_bucket" "trading-notifications-s3-bucket" {
  bucket = "trading-notifications-snow-leopard-1"
}

resource "aws_secretsmanager_secret" "trading-notifications-secrets" {
  name        = "trading-notifications-secrets"
  description = "Stores eodhd api key and app configuration"
}
