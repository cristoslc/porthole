# Porthole

Private remote access for a personal fleet of machines.

Run a bootstrap on any Linux, macOS, or Windows machine and it joins a
hub-and-spoke network — reachable from every other node in the fleet via SSH,
remote desktop, or both, through NAT, without port forwarding.

**Managed by:** `porthole` CLI
**Transport:** WireGuard (hub-and-spoke relay via VPS)
**Hostnames:** CoreDNS (`alice.wg`, `homelab.wg`, …)
**Remote desktop:** Apache Guacamole behind Caddy
**Fallback access:** SSH reverse tunnels

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | CLI is a pip-installable package |
| [uv](https://github.com/astral-sh/uv) | Recommended for local installs |
| [SOPS](https://github.com/getsops/sops) | Encrypts `network.sops.yaml` at rest |
| [age](https://github.com/FiloSottile/age) | Key backend for SOPS |
| SSH access to the hub VPS | `root` or passwordless `sudo`; ssh-agent forwarding recommended |
| A VPS running Ubuntu 22.04+ | Any cloud provider; minimum 1 vCPU / 512 MB RAM |

---

## Installation

```bash
git clone <repo-url> porthole
cd porthole
uv pip install -e .
```

Verify:

```bash
porthole --version
```

---

## Concepts

| Term | Description |
|------|-------------|
| **Hub** | The VPS. Runs the WireGuard server, CoreDNS, nftables, and Guacamole. All nodes connect to it. |
| **Node** | Any machine in the fleet (workstation, server, family machine). |
| **Role** | `workstation` — SSH + remote desktop. `server` — SSH only. `family` — SSH only, passive after setup. |
| **State file** | `network.sops.yaml` — encrypted YAML holding all keys and node definitions. |

---

## Quick Start

### 1. Generate an age key

```bash
age-keygen -o key.txt
# Copy the public key line: age1...
```

### 2. Initialize the network

```bash
porthole init \
  --endpoint hub.example.com:51820 \
  --age-key age1...
```

Creates `network.sops.yaml` and `.sops.yaml` in the current directory.

### 3. Bootstrap the hub VPS

Run once on a fresh Ubuntu VPS. Installs WireGuard, CoreDNS, nftables, and Docker.

```bash
porthole bootstrap hub.example.com
```

### 4. Register nodes

```bash
porthole add alice --role workstation
porthole add homelab --role server
porthole add moms-mac --role family
```

Each node gets a stable IP on `10.100.0.0/24` and a hostname (`alice.wg`, etc.).

### 5. Push hub config

```bash
porthole sync
```

Uploads the updated WireGuard, CoreDNS, and nftables configs to the hub.
Use `--dry-run` to preview rendered configs before deploying.

### 6. Generate per-node service files

```bash
porthole gen-peer-scripts alice
# Output: peer-scripts/alice/
```

Generated files:

- **WireGuard watchdog** — checks connectivity, restarts WireGuard if the hub is unreachable.
- **SSH reverse tunnel** — persistent reverse tunnel to the hub for fallback when WireGuard is unavailable.
- **Status HTTP server** — local web server on port 8888 showing node connectivity (LAN-visible).

Install by following the printed instructions (systemd on Linux, LaunchDaemons on macOS).

---

## Command Reference

| Command | Description |
|---------|-------------|
| `porthole init` | Initialize the network; create encrypted state file |
| `porthole add <name>` | Register a node (`--role workstation\|server\|family`) |
| `porthole remove <name>` | Remove a node from the network |
| `porthole list` | List all registered nodes (`--json` for machine-readable output) |
| `porthole sync` | Push hub configs (WireGuard, CoreDNS, nftables) to the VPS (`--dry-run` to preview) |
| `porthole gen-peer-scripts <name>` | Render watchdog + tunnel + status service files for a node |
| `porthole bootstrap <hub-host>` | One-time VPS bootstrap (packages, services, initial config) |
| `porthole status` | Query live WireGuard peer status from the hub |
| `porthole dashboard` | Run a local web dashboard showing fleet node status (`--port`, default 8080) |
| `porthole seed-guac` | Generate Guacamole connection seed SQL from current node list |

---

## Hub Setup (one-time extras after bootstrap)

### Restricted tunnel user

Nodes open reverse SSH tunnels using a `tunnel` OS user with no shell access.
Run once on the VPS:

```bash
sudo bash scripts/tunnel-user-setup.sh
```

Then for each node, append its tunnel public key to
`/home/tunnel/.ssh/authorized_keys` with the `command=...` restriction prefix
printed by the script.

### Guacamole (browser remote desktop)

```bash
cd deploy/guacamole
docker compose up -d
```

Caddy terminates TLS; configure your domain in `Caddyfile`. Seed initial
connections from the network state:

```bash
porthole seed-guac | docker exec -i guacamole-db psql -U guacamole
```

---

## State File

`network.sops.yaml` is encrypted with your age key. Commit it to version
control — private keys are never stored in plaintext. Keep your age key safe;
losing it means regenerating all node keys.

Inspect the decrypted state:

```bash
sops -d network.sops.yaml
```

---

## Node Roles

| Role | WireGuard | SSH | Remote Desktop |
|------|-----------|-----|----------------|
| `workstation` | Yes | Yes | Yes (via Guacamole) |
| `server` | Yes | Yes | No |
| `family` | Yes | Yes | No |

---

## Architecture

```
[Operator laptop]
       |
       | porthole CLI  (reads network.sops.yaml)
       |
       v
[Hub VPS: hub.example.com]
  - WireGuard     wg0  10.100.0.1  :51820
  - CoreDNS       *.wg zone
  - nftables      isolation rules
  - Guacamole     browser remote desktop
  - Caddy         TLS termination
  - sshd          reverse tunnel receiver  :2200-2220
       |
       |  WireGuard hub-and-spoke
       |
  [alice.wg  10.100.0.x]     [homelab.wg  10.100.0.y]
  wg-quick + watchdog         wg-quick + watchdog
  ssh-tunnel (fallback)       ssh-tunnel (fallback)
  wg-status-server :8888
```

---

## Development

```bash
uv pip install -e ".[dev]"
pytest
```
