terraform {
  required_providers {
    hetznerdns = {
      source  = "timohirt/hetznerdns"
      version = "~> 2.0"
    }
  }
}

variable "domain_name" {
  description = "Hetzner DNS zone name (parent domain, e.g. example.com)."
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

variable "apitoken" {
  description = "Hetzner Cloud/DNS API token."
  type        = string
  sensitive   = true
}

data "hetznerdns_zone" "hub" {
  name = var.domain_name
}

resource "hetznerdns_record" "hub_a" {
  zone_id = data.hetznerdns_zone.hub.id
  type    = "A"
  name    = var.subdomain
  value   = var.ip
  ttl     = 300
}

output "record_id" {
  value = hetznerdns_record.hub_a.id
}
