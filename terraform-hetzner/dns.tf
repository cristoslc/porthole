# ---------------------------------------------------------------------------
# dns.tf — DNS A record for the hub hostname via Hetzner DNS
#
# Hetzner Cloud and Hetzner DNS share the same API token (hcloud_token /
# var.hcloud_token). The hetznerdns provider handles DNS zone management.
#
# Prerequisite: the parent domain (e.g. "example.com") must already exist
# as a Hetzner-managed DNS zone. Terraform will not create or destroy the
# zone itself — only the A record for the hub subdomain.
#
# Example: hub_hostname = "hub.example.com" → looks up zone "example.com"
# and creates an A record for subdomain "hub".
# ---------------------------------------------------------------------------

locals {
  hostname_parts = split(".", var.hub_hostname)
  subdomain      = local.hostname_parts[0]
  domain_name    = join(".", slice(local.hostname_parts, 1, length(local.hostname_parts)))
}

data "hetznerdns_zone" "hub" {
  name = local.domain_name
}

resource "hetznerdns_record" "hub_a" {
  zone_id = data.hetznerdns_zone.hub.id
  type    = "A"
  name    = local.subdomain
  value   = hcloud_server.hub.ipv4_address
  ttl     = 300
}
