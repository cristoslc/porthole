# ---------------------------------------------------------------------------
# main.tf — Hub VPS, SSH key, and firewall
#
# Reference provider: DigitalOcean
# To adapt to another provider, swap the resource types below and update
# versions.tf + variables.tf. The logical structure stays the same.
# ---------------------------------------------------------------------------

provider "digitalocean" {
  token = var.do_token
}

# ---------------------------------------------------------------------------
# SSH key
# ---------------------------------------------------------------------------

resource "digitalocean_ssh_key" "hub" {
  name       = "${var.hub_hostname}-key"
  public_key = file(var.ssh_key_path)
}

# ---------------------------------------------------------------------------
# Droplet (VPS)
# ---------------------------------------------------------------------------

resource "digitalocean_droplet" "hub" {
  name     = var.hub_hostname
  region   = var.region
  size     = var.droplet_size
  image    = "ubuntu-22-04-x64"
  ssh_keys = [digitalocean_ssh_key.hub.fingerprint]

  # Ensure the firewall is applied before traffic can reach the Droplet.
  depends_on = [digitalocean_firewall.hub]

  tags = ["porthole", "hub"]
}

# ---------------------------------------------------------------------------
# Firewall / security group
#
# Inbound rules:
#   - TCP 22    — SSH management
#   - UDP 51820 — WireGuard VPN
#   - TCP 443   — HTTPS (Porthole web UI / API)
#   - TCP 80    — HTTP (redirect to HTTPS / Let's Encrypt challenge)
#
# All other inbound traffic is denied implicitly.
# All outbound traffic is permitted.
# ---------------------------------------------------------------------------

resource "digitalocean_firewall" "hub" {
  name        = "${var.hub_hostname}-fw"
  droplet_ids = [digitalocean_droplet.hub.id]

  # SSH
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # WireGuard
  inbound_rule {
    protocol         = "udp"
    port_range       = "51820"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTP (Let's Encrypt / redirect)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Reverse SSH tunnel listening ports (2200 + last octet of each peer IP)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "2200-2220"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # ICMP
  inbound_rule {
    protocol         = "icmp"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow all outbound traffic
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
