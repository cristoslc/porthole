terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "zone_name" {
  description = "Cloudflare DNS zone name (parent domain, e.g. example.com)."
  type        = string
}

variable "subdomain" {
  description = "Subdomain label to create (e.g. hub)."
  type        = string
}

variable "ip" {
  description = "IPv4 address for the A record."
  type        = string
}

variable "api_token" {
  description = "Cloudflare API token."
  type        = string
  sensitive   = true
}

data "cloudflare_zone" "hub" {
  name = var.zone_name
}

resource "cloudflare_record" "hub_a" {
  zone_id = data.cloudflare_zone.hub.id
  type    = "A"
  name    = var.subdomain
  content = var.ip
  ttl     = 300
  proxied = false
}

output "record_id" {
  value = cloudflare_record.hub_a.id
}
