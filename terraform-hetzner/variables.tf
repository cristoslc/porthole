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
# Provider-portability note
# ---------------------------------------------------------------------------
# This Hetzner implementation mirrors the DigitalOcean reference in terraform/.
# The logical structure (VPS + SSH key + firewall + DNS) is identical; only
# the provider-specific resource types differ.
