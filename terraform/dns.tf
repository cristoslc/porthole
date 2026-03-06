# ---------------------------------------------------------------------------
# dns.tf — Pluggable DNS A record for the hub hostname
#
# Set var.dns_provider to activate the appropriate module:
#   cloudflare   — uses cloudflare/cloudflare provider (CLOUDFLARE_API_TOKEN)
#   digitalocean — uses digitalocean/digitalocean provider (TF_VAR_do_token)
#   hetzner      — uses timohirt/hetznerdns provider (TF_VAR_hcloud_token)
#   none         — no DNS record created; manage DNS manually
#
# Prerequisite: the parent domain must already exist as a zone in the chosen
# provider. Terraform creates only the A record for the hub subdomain.
#
# Example: hub_hostname = "hub.example.com"
#   → zone/domain = "example.com", subdomain = "hub"
# ---------------------------------------------------------------------------

locals {
  hostname_parts = split(".", var.hub_hostname)
  subdomain      = local.hostname_parts[0]
  domain_name    = join(".", slice(local.hostname_parts, 1, length(local.hostname_parts)))
}

module "dns_cloudflare" {
  count  = var.dns_provider == "cloudflare" ? 1 : 0
  source = "./modules/dns_cloudflare"

  zone_name = local.domain_name
  subdomain = local.subdomain
  ip        = digitalocean_droplet.hub.ipv4_address
  api_token = var.cloudflare_api_token

  providers = {
    cloudflare = cloudflare
  }
}

module "dns_digitalocean" {
  count  = var.dns_provider == "digitalocean" ? 1 : 0
  source = "./modules/dns_digitalocean"

  domain    = local.domain_name
  subdomain = local.subdomain
  ip        = digitalocean_droplet.hub.ipv4_address
  do_token  = var.do_token

  providers = {
    digitalocean = digitalocean
  }
}

module "dns_hetzner" {
  count  = var.dns_provider == "hetzner" ? 1 : 0
  source = "./modules/dns_hetzner"

  domain_name = local.domain_name
  subdomain   = local.subdomain
  ip          = digitalocean_droplet.hub.ipv4_address
  apitoken    = var.hcloud_token

  providers = {
    hetznerdns = hetznerdns
  }
}
