# ---------------------------------------------------------------------------
# dns.tf — DNS A record for the hub hostname
#
# Prerequisite: the parent domain (e.g. "example.com") must already exist
# as a DigitalOcean-managed domain. This configuration looks it up via a
# data source; Terraform will not create or destroy the domain itself.
#
# Example: if hub_hostname = "hub.example.com", the data source looks up
# "example.com" and creates an A record for the subdomain "hub".
# ---------------------------------------------------------------------------

locals {
  # Split "hub.example.com" into subdomain="hub" and domain="example.com".
  # Works for a single-level subdomain. Adjust the index if deeper nesting
  # is required (e.g. "vpn.hub.example.com").
  hostname_parts = split(".", var.hub_hostname)
  subdomain      = local.hostname_parts[0]
  domain_name    = join(".", slice(local.hostname_parts, 1, length(local.hostname_parts)))
}

# Look up the existing DigitalOcean domain — must already exist.
data "digitalocean_domain" "hub" {
  name = local.domain_name
}

# Create an A record pointing the hub subdomain at the Droplet's public IP.
resource "digitalocean_record" "hub_a" {
  domain = data.digitalocean_domain.hub.id
  type   = "A"
  name   = local.subdomain
  value  = digitalocean_droplet.hub.ipv4_address
  ttl    = 300
}
