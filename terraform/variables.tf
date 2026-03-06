variable "do_token" {
  description = "DigitalOcean personal access token. Set via TF_VAR_do_token environment variable or a .tfvars file. Never commit this value."
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# DNS provider selection
# ---------------------------------------------------------------------------

variable "dns_provider" {
  description = "Which DNS provider to use for the hub A record. Set to 'none' to skip DNS (manage manually). Valid values: cloudflare, digitalocean, hetzner, none."
  type        = string
  default     = "none"

  validation {
    condition     = contains(["cloudflare", "digitalocean", "hetzner", "none"], var.dns_provider)
    error_message = "dns_provider must be one of: cloudflare, digitalocean, hetzner, none."
  }
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token. Required when dns_provider = cloudflare. Set via TF_VAR_cloudflare_api_token or CLOUDFLARE_API_TOKEN."
  type        = string
  sensitive   = true
  default     = ""
}

variable "hcloud_token" {
  description = "Hetzner Cloud/DNS API token. Required when dns_provider = hetzner. Set via TF_VAR_hcloud_token."
  type        = string
  sensitive   = true
  default     = ""
}

variable "region" {
  description = "DigitalOcean region slug where the hub Droplet will be created."
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "DigitalOcean Droplet size slug for the hub node."
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "hub_hostname" {
  description = "Fully-qualified hostname for the hub (e.g. hub.example.com). Used for the DNS A record and as the Droplet name."
  type        = string
}

variable "ssh_key_path" {
  description = "Path on the local machine to the SSH public key file that will be installed on the hub Droplet."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

