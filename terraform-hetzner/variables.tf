variable "hcloud_token" {
  description = "Hetzner Cloud API token. Set via TF_VAR_hcloud_token environment variable or a .tfvars file. Never commit this value."
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Hetzner Cloud location for the hub server (e.g. nbg1, fsn1, hel1, ash, hil)."
  type        = string
  default     = "nbg1"
}

variable "server_type" {
  description = "Hetzner Cloud server type slug for the hub node."
  type        = string
  default     = "cx22"
}

variable "hub_hostname" {
  description = "Fully-qualified hostname for the hub (e.g. hub.example.com). Used for the DNS A record and server name."
  type        = string
}

variable "ssh_key_path" {
  description = "Path on the local machine to the SSH public key file that will be installed on the hub server."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
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

variable "do_token" {
  description = "DigitalOcean API token for DNS. Required when dns_provider = digitalocean. Set via TF_VAR_do_token."
  type        = string
  sensitive   = true
  default     = ""
}

# ---------------------------------------------------------------------------
# Provider-portability note
# ---------------------------------------------------------------------------
# This Hetzner implementation mirrors the DigitalOcean reference in terraform/.
# The logical structure (VPS + SSH key + firewall + DNS) is identical; only
# the provider-specific resource types differ.
