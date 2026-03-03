terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

variable "domain" {
  description = "DigitalOcean DNS domain (zone) name, e.g. example.com."
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

variable "do_token" {
  description = "DigitalOcean API token."
  type        = string
  sensitive   = true
}

resource "digitalocean_record" "hub_a" {
  domain = var.domain
  type   = "A"
  name   = var.subdomain
  value  = var.ip
  ttl    = 300
}

output "record_id" {
  value = digitalocean_record.hub_a.id
}
