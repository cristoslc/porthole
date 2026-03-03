# ---------------------------------------------------------------------------
# main.tf — Hub server, SSH key, and firewall
#
# Provider: Hetzner Cloud (hcloud)
# Reference implementation: terraform/ (DigitalOcean)
#
# NOTE: Run with HashiCorp terraform (not tofu). The hetznerdns provider is
# only available in the Terraform registry, not the OpenTofu registry.
#   brew tap hashicorp/tap && brew install hashicorp/tap/terraform
# ---------------------------------------------------------------------------

provider "hcloud" {
  token = var.hcloud_token
}

provider "hetznerdns" {
  apitoken = var.hcloud_token
}

# ---------------------------------------------------------------------------
# SSH key
# ---------------------------------------------------------------------------

resource "hcloud_ssh_key" "hub" {
  name       = "${var.hub_hostname}-key"
  public_key = file(var.ssh_key_path)
}

# ---------------------------------------------------------------------------
# Firewall
#
# Inbound rules:
#   - TCP 22         — SSH management
#   - UDP 51820      — WireGuard VPN
#   - TCP 443        — HTTPS (Porthole web UI / API)
#   - TCP 80         — HTTP (redirect to HTTPS / Let's Encrypt challenge)
#   - TCP 2200-2220  — Reverse SSH tunnel ports (2200 + last octet of peer IP)
#   - ICMP           — ping
#
# All other inbound traffic is denied by default.
# All outbound traffic is permitted (Hetzner's default).
# ---------------------------------------------------------------------------

resource "hcloud_firewall" "hub" {
  name = "${var.hub_hostname}-fw"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "udp"
    port       = "51820"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "2200-2220"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# ---------------------------------------------------------------------------
# Server (VPS)
# ---------------------------------------------------------------------------

resource "hcloud_server" "hub" {
  name         = var.hub_hostname
  location     = var.location
  server_type  = var.server_type
  image        = "ubuntu-22.04"
  ssh_keys     = [hcloud_ssh_key.hub.name]
  firewall_ids = [hcloud_firewall.hub.id]

  labels = {
    project = "porthole"
    role    = "hub"
  }
}
