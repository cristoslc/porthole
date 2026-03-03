variable "do_token" {
  description = "DigitalOcean personal access token. Set via TF_VAR_do_token environment variable or a .tfvars file. Never commit this value."
  type        = string
  sensitive   = true
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

# ---------------------------------------------------------------------------
# Provider-portability note
# ---------------------------------------------------------------------------
# The variables above map to DigitalOcean concepts. Adapting to another
# cloud provider (Hetzner, Vultr, Linode, etc.) requires:
#   1. Replacing the provider block in versions.tf.
#   2. Replacing resource types in main.tf and dns.tf.
#   3. Renaming or aliasing provider-specific variables (e.g. do_token ->
#      hcloud_token) and updating variable descriptions accordingly.
# The logical structure (VPS + SSH key + firewall + DNS) remains the same
# across providers; only the resource type names change.
