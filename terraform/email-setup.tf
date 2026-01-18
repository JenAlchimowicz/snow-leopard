# 1. Fetch your existing Route 53 zone
# This looks for the domain you already have in your AWS account
data "aws_route53_zone" "selected" {
  name         = "mlprojectsbyjen.com"
  private_zone = false
}

# 2. Create the SES Domain Identity
resource "aws_ses_domain_identity" "ses_example" {
  domain = data.aws_route53_zone.selected.name
}

# 3. Generate DKIM security tokens
resource "aws_ses_domain_dkim" "ses_example" {
  domain = aws_ses_domain_identity.ses_example.domain
}

# 4. Automatically add DKIM records to your existing Route 53 DNS
resource "aws_route53_record" "example_dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = "${element(aws_ses_domain_dkim.ses_example.dkim_tokens, count.index)}._domainkey"
  type    = "CNAME"
  ttl     = "600"
  records = ["${element(aws_ses_domain_dkim.ses_example.dkim_tokens, count.index)}.dkim.amazonses.com"]
}
