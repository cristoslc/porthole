---
title: "Porthole CLI and TUI for Nebula"
artifact: DESIGN-001
status: Draft
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
superseded-by:
linked-epics:
  - EPIC-001
  - EPIC-007
linked-stories: []
linked-specs:
  - SPEC-003
  - SPEC-008
  - SPEC-009
linked-bugs: []
linked-adrs:
  - ADR-008
  - ADR-006
depends-on:
  - ADR-008
---

# DESIGN-001: Porthole CLI and TUI for Nebula

## Interaction Surface

The complete operator-facing interface for managing a Nebula overlay network: the `porthole` CLI (13 commands → redesigned for Nebula) and the `porthole-setup` TUI (7-screen wizard for node enrollment). This design replaces the WireGuard-based CLI (SPEC-003) with a Nebula-native design per ADR-008.

**Scope:** Everything the operator types or sees. Not the system internals (Spec), not the user journey narrative (Journey), not the hub infrastructure (SPEC-008).

## What changes, what stays

### Stays the same
- Click CLI framework, Textual TUI framework
- SOPS/age encryption for state at rest
- Jinja2 template rendering pipeline
- CoreDNS zone generation
- Guacamole SQL seeding
- IP allocation from subnet pool
- TUI screen progression (prerequisites → secrets → hub check → spinup → enroll → services → summary)
- `setup.sh` bash shim entry point

### Changes fundamentally
- **Key generation** → replaced by CA certificate management + per-peer cert signing
- **`sync` command** → eliminated (lighthouse discovers peers from certs)
- **Hub config rendering** → lighthouse config instead of wg0.conf
- **Peer config rendering** → Nebula config.yml + cert bundle instead of wg0.conf
- **`bootstrap`** → Nebula lighthouse deployment instead of WireGuard + nftables
- **Service files** → `nebula` service instead of `wg-quick` + watchdog
- **`status`** → Nebula handshake status instead of `wg show dump`
- **Firewall** → Nebula's built-in group-based rules replace hub nftables
- **Hub check screen** → no SSH setup key, no temporary SSH window dance

## CLI Commands

### Redesigned command set

| Command | Arguments | What it does | Nebula operations |
|---------|-----------|-------------|-------------------|
| `porthole init` | `--endpoint`, `--age-key`, `--domain` | Initialize network: create CA, lighthouse config, encrypt state | `nebula-cert ca` → CA key + cert; store in `network.sops.yaml` |
| `porthole add` | `name`, `--role`, `--platform`, `--dns-name`, `--groups` | Add peer: sign cert, allocate IP, store in state | `nebula-cert sign` → peer cert + key; NO hub update needed |
| `porthole remove` | `name` | Remove peer from state | Revoke cert (add to blocklist in lighthouse config); no hub sync needed for simple removal |
| `porthole list` | `--json` | List all peers | Read state, display table with name/IP/groups/role |
| `porthole peer-config` | `name`, `--out` | Output Nebula config bundle for a peer | Render `config.yml` from template + write cert/key files |
| `porthole gen-peer-scripts` | `name`, `--out` | Generate service files for a peer | Render systemd/launchd/Windows service files for `nebula` |
| `porthole install-peer` | `name`, `--host` | Install config + service on a peer via SSH | SCP config bundle, enable nebula service |
| `porthole bootstrap` | `hub_host` | Provision lighthouse on a VPS | Deploy nebula binary + lighthouse config + CoreDNS + Guacamole |
| `porthole status` | — | Show live peer status from lighthouse | SSH to lighthouse, parse nebula status or query admin API |
| `porthole dashboard` | `--port` | Run local web dashboard | HTTP server showing fleet status |
| `porthole seed-guac` | `--out`, `--apply` | Generate Guacamole seed SQL | Unchanged — reads peer IPs from state |
| `porthole enroll` | `name` | Transfer config bundle to a peer | Magic Wormhole or manual copy of cert + config bundle |

### Commands removed

| Old command | Why removed |
|-------------|-------------|
| `porthole sync` | **Eliminated.** Nebula lighthouse discovers peers from their signed certificates. No hub config update needed when adding or removing peers. This was the entire point of switching to Nebula (ADR-008). |

### Commands changed significantly

**`porthole init`** — the biggest change:

```
Old (WireGuard):
  1. Generate hub WG keypair (wg genkey | wg pubkey)
  2. Create network state with hub peer entry
  3. Encrypt with sops

New (Nebula):
  1. Generate CA keypair (nebula-cert ca -name "porthole-ca")
  2. Sign lighthouse certificate (nebula-cert sign -name "lighthouse" -ip "10.100.0.1/24" -groups "lighthouse")
  3. Create network state with CA cert/key + lighthouse entry
  4. Encrypt with sops
```

**`porthole add`** — no hub interaction:

```
Old (WireGuard):
  1. Generate WG keypair
  2. Allocate IP
  3. Add peer to state
  4. MUST run `porthole sync` to update hub config ← this is eliminated

New (Nebula):
  1. Allocate IP
  2. Sign certificate (nebula-cert sign -name "peer-name" -ip "10.100.0.N/24" -groups "workstation")
  3. Add peer to state
  4. Done. Lighthouse discovers peer when it connects.
```

**`porthole remove`** — optional lighthouse update:

```
Old (WireGuard):
  1. Remove peer from state
  2. MUST run `porthole sync` to remove peer from hub wg0.conf

New (Nebula):
  1. Remove peer from state
  2. Optionally add cert fingerprint to lighthouse's blocklist
     (Nebula certs have an expiry — removed peers naturally age out.
      Blocklist is for immediate revocation before expiry.)
```

## State Schema

### `network.sops.yaml` — redesigned

```yaml
# Nebula CA (SOPS-encrypted)
ca:
  cert: |
    -----BEGIN NEBULA CERTIFICATE-----
    ...
    -----END NEBULA CERTIFICATE-----
  key: |                              # SOPS-encrypted field
    -----BEGIN NEBULA ED25519 PRIVATE KEY-----
    ...
    -----END NEBULA ED25519 PRIVATE KEY-----

# Network config
network:
  subnet: "10.100.0.0/24"
  domain: "wg"                        # DNS domain for CoreDNS (.wg)
  lighthouse_port: 4242               # Nebula UDP port
  cert_duration: "8760h"              # 1 year default cert validity

# Lighthouse (hub)
lighthouse:
  name: "lighthouse"
  endpoint: "hub.example.com"
  ip: "10.100.0.1"
  cert: |
    -----BEGIN NEBULA CERTIFICATE-----
    ...
    -----END NEBULA CERTIFICATE-----
  key: |                              # SOPS-encrypted field
    -----BEGIN NEBULA ED25519 PRIVATE KEY-----
    ...
    -----END NEBULA ED25519 PRIVATE KEY-----
  groups:
    - lighthouse

# Peers
peers:
  - name: "workstation-1"
    ip: "10.100.0.2"
    dns_name: "ws1"
    role: "workstation"               # workstation, server, family
    platform: "linux"                 # linux, macos, windows
    groups:                           # Nebula certificate groups
      - workstation
    cert: |
      -----BEGIN NEBULA CERTIFICATE-----
      ...
      -----END NEBULA CERTIFICATE-----
    key: |                            # SOPS-encrypted field
      -----BEGIN NEBULA ED25519 PRIVATE KEY-----
      ...
      -----END NEBULA ED25519 PRIVATE KEY-----
    reverse_ssh_port: 2202            # For fallback recovery (SPIKE-006)

# Guacamole
guacamole:
  admin_password: "..."               # SOPS-encrypted field

# Certificate blocklist (revoked peers)
blocklist: []                         # Cert fingerprints of revoked peers
```

### Key differences from WireGuard schema

| Field | WireGuard | Nebula |
|-------|-----------|--------|
| Hub identity | `public_key` + `private_key` (WG keypair) | `cert` + `key` (signed certificate) |
| Peer identity | `public_key` + `private_key` (WG keypair) | `cert` + `key` (CA-signed certificate) |
| CA | None | `ca.cert` + `ca.key` — the root of trust |
| Groups | None (role field, but not used by WG) | Certificate groups used by Nebula firewall |
| Port | `51820` (WireGuard) | `4242` (Nebula default) |
| Blocklist | None | Cert fingerprints for immediate revocation |
| Cert duration | N/A | Configurable expiry for signed certs |

## TUI Screens

### Screen 1: Prerequisites (minor changes)

**Was:** Install wg, sops, age, terraform, porthole via ansible
**Now:** Install **nebula**, sops, age, terraform, porthole via ansible

Change: Replace `wireguard-tools` package with `nebula` binary. The ansible playbook downloads the nebula release binary for the platform.

### Screen 2: Secrets (unchanged)

Generate age key, write `.sops.yaml`. No changes — the encryption layer is orthogonal to the tunnel layer.

### Screen 3: Hub Check (simplified)

**Was:**
- Load `network.sops.yaml`
- If missing: show endpoint input + "Initialize" button → runs `porthole init --endpoint X --age-key Y`
- If present: DNS resolution check (informational), always show Continue
- Buttons: Continue, Spin Up Hub, Re-initialize, Re-check, Back

**Now:** Same flow, but:
- Remove any SSH-related UI (no setup key, no `hub-ssh-open`/`hub-ssh-close`)
- The "Initialize" step runs `porthole init` which now creates Nebula CA + lighthouse cert
- Hub reachability check: attempt Nebula handshake or just DNS resolve (informational)

### Screen 4: Hub Spinup (lighthouse instead of WG hub)

**Was:** `terraform apply` + `ansible-playbook` → provisions WireGuard + CoreDNS + nftables + Guacamole
**Now:** `terraform apply` + `ansible-playbook` → provisions **Nebula lighthouse** + CoreDNS + Guacamole

Cloud-init injects:
- Nebula lighthouse binary + config + CA cert + lighthouse cert/key
- CoreDNS config
- Guacamole Docker stack

No nftables — Nebula's built-in firewall handles access control.

### Screen 4b: Enrollment (simplified — no sync needed)

**Was:**
1. Run `porthole add` to register this node in state
2. Run `porthole sync` to push updated config to hub ← **this step is eliminated**
3. Generate peer scripts

**Now:**
1. Run `porthole add` to register this node (signs cert with CA key)
2. Generate peer config bundle (cert + key + config.yml)
3. Done — lighthouse discovers this node when nebula starts

The elimination of `sync` is the most visible UX improvement. The operator goes from `add → sync → gen-scripts` to just `add → gen-scripts`.

### Screen 4c: Service Install (nebula instead of wg-quick)

**Was:** Copy wg0.conf + watchdog scripts + SSH tunnel service → enable systemd/launchd units
**Now:** Copy nebula config.yml + cert + key → enable `nebula` service

Simpler — one service (`nebula`) instead of three (wg-quick + watchdog + ssh-tunnel). The watchdog is less critical because Nebula handles reconnection natively.

### Screen 5: Summary (updated labels)

Replace "WireGuard" with "Nebula" in status checklist items. Check for `nebula` service running instead of `wg0` interface.

## Nebula Config Templates

### Lighthouse config (`lighthouse-config.yml.j2`)

```yaml
pki:
  ca: /etc/nebula/ca.crt
  cert: /etc/nebula/lighthouse.crt
  key: /etc/nebula/lighthouse.key
  blocklist:
{% for fp in blocklist %}
    - {{ fp }}
{% endfor %}

lighthouse:
  am_lighthouse: true

listen:
  host: 0.0.0.0
  port: {{ lighthouse_port }}

punchy:
  punch: true

firewall:
  outbound:
    - port: any
      proto: any
      host: any
  inbound:
    - port: any
      proto: icmp
      host: any
    - port: 22
      proto: tcp
      groups:
        - workstation
        - server
        - lighthouse
    - port: 3389
      proto: tcp
      groups:
        - workstation
    - port: 5900
      proto: tcp
      groups:
        - workstation
    # Guacamole web UI — lighthouse only
    - port: 443
      proto: tcp
      groups:
        - workstation
        - server
```

### Peer config (`peer-config.yml.j2`)

```yaml
pki:
  ca: /etc/nebula/ca.crt
  cert: /etc/nebula/{{ peer_name }}.crt
  key: /etc/nebula/{{ peer_name }}.key

static_host_map:
  "{{ lighthouse_ip }}": ["{{ lighthouse_endpoint }}:{{ lighthouse_port }}"]

lighthouse:
  am_lighthouse: false
  hosts:
    - "{{ lighthouse_ip }}"

listen:
  host: 0.0.0.0
  port: 0                              # Random port — not a lighthouse

punchy:
  punch: true

firewall:
  outbound:
    - port: any
      proto: any
      host: any
  inbound:
    - port: any
      proto: icmp
      host: any
    - port: 22
      proto: tcp
      groups:
        - workstation
        - server
        - lighthouse
```

## Edge Cases and Error States

### CA key not available
If `network.sops.yaml` can't be decrypted (age key missing), `porthole add` fails with a clear error: "Cannot sign certificate — age key required to decrypt CA key. Run `porthole-setup` to configure secrets."

### Lighthouse unreachable after init
The lighthouse must be provisioned before peers can connect. If a peer is added but the lighthouse isn't running, the peer's nebula service will retry connection in the background. The TUI's hub check screen detects this and offers the spinup flow.

### Certificate expiry
Certs have a configurable duration (default 1 year). A future `porthole renew` command could re-sign expiring certs. For MVP, manual re-signing via `porthole add --force` (re-signs cert for existing peer) is sufficient.

### Peer revocation
`porthole remove` adds the peer's cert fingerprint to the blocklist in state. The blocklist is deployed to the lighthouse config. For immediate effect, the lighthouse config must be re-deployed — this is the one case where an SSH-to-lighthouse operation remains (via Ansible). However, cert expiry provides a natural revocation timeline.

### Platform-specific nebula paths
| Platform | Binary | Config dir | Service |
|----------|--------|-----------|---------|
| Linux | `/usr/local/bin/nebula` | `/etc/nebula/` | `systemd` unit |
| macOS | `/usr/local/bin/nebula` | `/etc/nebula/` | `launchd` plist |
| Windows | `C:\Program Files\Nebula\nebula.exe` | `C:\Program Files\Nebula\` | `nebula.exe service install` |

## Design Decisions

1. **No `sync` command.** The entire WireGuard `sync` workflow (SSH to hub, render config, reload) is eliminated. This is the primary UX win from Nebula adoption (ADR-008). Peers are enrolled by signing a certificate locally — the lighthouse discovers them automatically.

2. **Certificate groups map to roles.** The existing `role` field (workstation, server, family) maps directly to Nebula certificate groups. The firewall rules in the lighthouse config use these groups for access control. No separate nftables management.

3. **Blocklist for revocation, expiry for natural cleanup.** Removing a peer adds its cert fingerprint to a blocklist. This is deployed to the lighthouse config via Ansible. Certs also have a natural expiry, so even without blocklist deployment, a removed peer eventually loses access.

4. **`enroll` replaces config transfer.** A new `porthole enroll` command handles the "get config to the peer" step, using Magic Wormhole for zero-config transfer or `--manual` for direct file copy. This replaces the ad-hoc `peer-config | scp` pattern.

5. **Single service per node.** WireGuard required wg-quick + watchdog timer + SSH tunnel service. Nebula is a single binary with built-in reconnection (`punchy`), so one service unit suffices. The SSH tunnel service for reverse access fallback (SPIKE-006 Layer 2) remains available as an optional add-on.

6. **Watchdog simplified.** Nebula handles its own reconnection via `punchy`. The watchdog script (Layer 1 of SPIKE-006's recovery model) is reduced to a health check that restarts the nebula service if it's unresponsive, rather than the complex DNS re-resolution + WireGuard reload cycle.

## Assets

| File | Description |
|------|-------------|
| [cli-command-map.md](./cli-command-map.md) | Detailed before/after mapping of every CLI command |
| (future) TUI wireframes | Screen mockups if interaction changes warrant them |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-07 | — | Initial design based on ADR-008 adoption and existing CLI inventory |
