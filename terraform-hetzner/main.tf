# ---------------------------------------------------------------------------
# main.tf — Hub server, SSH key, and firewall
#
# Provider: Hetzner Cloud (hcloud)
# Reference implementation: terraform/ (DigitalOcean)
# ---------------------------------------------------------------------------

provider "hcloud" {
  token = var.hcloud_token
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
#   - TCP 22    — SSH management
#   - UDP 51820 — WireGuard VPN
#   - TCP 443   — HTTPS (Porthole web UI / API)
#   - TCP 80    — HTTP (redirect to HTTPS / Let's Encrypt challenge)
#
# All other inbound traffic is denied by default.
# All outbound traffic is permitted (Hetzner's default; no explicit rule needed).
# ---------------------------------------------------------------------------

resource "hcloud_firewall" "hub" {
  name = "${var.hub_hostname}-fw"

  # SSH
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # WireGuard
  rule {
    direction  = "in"
    protocol   = "udp"
    port       = "51820"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTP (Let's Encrypt / redirect)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # Reverse SSH tunnel ports (2200 + last octet of each peer IP)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "2200-2220"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # ICMP (ping)
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
