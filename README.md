# wgmesh

A WireGuard hub-and-spoke network management CLI. Bootstrap a VPS hub, register
peer machines, and generate per-peer service files — so every node in your fleet
can reach every other node by hostname, through NAT, without manual VPN
configuration.

**Stack:** WireGuard for the mesh · CoreDNS for `<name>.wg` hostnames · nftables
for isolation · Guacamole for browser-based remote desktop · SSH reverse tunnels
for fallback access.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | CLI is a pip-installable package |
| [uv](https://github.com/astral-sh/uv) | Recommended for local installs |
| [SOPS](https://github.com/getsops/sops) | Encrypts `network.sops.yaml` at rest |
| [age](https://github.com/FiloSottile/age) | Key backend for SOPS |
| SSH access to the hub VPS | `root` or passwordless `sudo`; `ssh-agent` forwarding recommended |
| A VPS running Ubuntu 22.04+ | Any cloud provider; minimum 1 vCPU / 512 MB RAM |

---

## Installation

```bash
# Clone and install in an editable virtualenv
git clone <repo-url> wgmesh
cd wgmesh
uv pip install -e .
```

Verify:

```bash
wgmesh --version
```

---

## Concepts

| Term | Description |
|------|-------------|
| **Hub** | The VPS. Holds the WireGuard server config, CoreDNS, and nftables rules. Every peer connects to it. |
| **Peer** | Any node you want in the fleet (workstation, server, family machine). |
| **Role** | `workstation` — SSH + remote desktop. `server` — SSH only. `family` — SSH only, treated as passive. |
| **State file** | `network.sops.yaml` — encrypted YAML holding all keys and peer definitions. Lives in your working directory. |

---

## Quick Start

### 1. Generate an age key

```bash
age-keygen -o key.txt
# Copy the public key line: age1...
```

### 2. Initialize the mesh

```bash
wgmesh init \
  --endpoint hub.example.com:51820 \
  --age-key age1...
```

Creates `network.sops.yaml` (encrypted) and `.sops.yaml` in the current directory.

### 3. Bootstrap the hub VPS

Run once on a fresh Ubuntu VPS. Installs WireGuard, CoreDNS, nftables, and Docker.

```bash
wgmesh bootstrap hub.example.com
```

### 4. Add peers

```bash
wgmesh add alice --role workstation
wgmesh add homelab --role server
wgmesh add moms-mac --role family
```

Each peer is assigned a stable IP on `10.100.0.0/24` and a hostname
(`alice.wg`, `homelab.wg`, etc.).

### 5. Sync hub config

Push the updated WireGuard, CoreDNS, and nftables configs to the hub:

```bash
wgmesh sync
```

Use `--dry-run` to preview rendered configs before deploying.

### 6. Generate per-peer service files

```bash
wgmesh gen-peer-scripts alice
# Output: peer-scripts/alice/
```

This generates:

- **WireGuard watchdog** — periodically checks connectivity and restarts WireGuard
  if the hub is unreachable.
- **SSH reverse tunnel service** — opens a persistent reverse tunnel back to the
  hub for fallback access when WireGuard is unavailable.
- **Status HTTP server** — tiny web server on port 8888 showing peer connectivity
  state (visible on the local LAN).

Install the files on the peer by following the printed instructions (systemd on
Linux, LaunchDaemons on macOS).

---

## Command Reference

```
wgmesh --help
```

| Command | Description |
|---------|-------------|
| `init` | Initialize a new mesh; create encrypted state file |
| `add <name>` | Add a peer (`--role workstation\|server\|family`) |
| `remove <name>` | Remove a peer from the mesh |
| `list` | List all registered peers (`--json` for machine-readable output) |
| `sync` | Push hub configs (WireGuard, CoreDNS, nftables) to the VPS (`--dry-run` to preview) |
| `gen-peer-scripts <name>` | Render watchdog + tunnel + status service files for a peer |
| `bootstrap <hub-host>` | One-time VPS bootstrap (packages, services, initial config) |
| `status` | Query live WireGuard peer status from the hub |
| `dashboard` | Run a local web dashboard showing fleet peer status (`--port`, default 8080) |
| `seed-guac` | Generate Guacamole connection seed SQL from current peer list |

---

## Hub VPS Setup (extra steps after bootstrap)

### Restricted tunnel user

Peers open reverse SSH tunnels to the hub using a dedicated `tunnel` user with
no shell access. Run once on the VPS:

```bash
sudo bash scripts/tunnel-user-setup.sh
```

Then for each peer, append its tunnel public key to
`/home/tunnel/.ssh/authorized_keys` with the `command=...` restriction prefix
printed by the script.

### Guacamole (browser remote desktop)

The `deploy/guacamole/` directory contains a Docker Compose stack for
[Apache Guacamole](https://guacamole.apache.org/) behind a Caddy reverse proxy.

```bash
cd deploy/guacamole
docker compose up -d
```

Caddy terminates TLS; configure your domain in `Caddyfile`. Seed initial
connections from the network state:

```bash
wgmesh seed-guac | docker exec -i guacamole-db psql -U guacamole
```

---

## State File

`network.sops.yaml` is encrypted with your age key. Commit it to version control
— private keys are never stored in plaintext. Keep your age key safe; losing it
means regenerating all peer keys.

To inspect the decrypted state:

```bash
sops -d network.sops.yaml
```

---

## Peer Roles

| Role | WireGuard | SSH (hub-side) | Remote Desktop |
|------|-----------|----------------|----------------|
| `workstation` | Yes | Yes | Yes (via Guacamole) |
| `server` | Yes | Yes | No |
| `family` | Yes | Yes | No |

---

## Architecture

```
[Operator machine]
       |
       | wgmesh CLI (reads network.sops.yaml)
       |
       v
[VPS Hub: hub.example.com]
  - WireGuard (wg0, 10.100.0.1)
  - CoreDNS   (*.wg zone)
  - nftables  (isolation rules)
  - Guacamole + Caddy (remote desktop)
  - SSH server (reverse tunnel receiver, port 2200-2220)
       |
       | WireGuard spoke connections
       |
  [Peer: alice.wg / 10.100.0.x]   [Peer: homelab.wg / 10.100.0.y]
  - wg-quick (WireGuard client)    - wg-quick (WireGuard client)
  - wg-watchdog (reconnect daemon) - wg-watchdog (reconnect daemon)
  - ssh-tunnel service (fallback)  - ssh-tunnel service (fallback)
  - wg-status-server (LAN UI)
```

---

## Development

```bash
uv pip install -e ".[dev]"
pytest
```
