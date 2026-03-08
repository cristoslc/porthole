---
title: "Porthole CLI for Nebula"
artifact: DESIGN-001
status: Draft
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
superseded-by:
linked-epics:
  - EPIC-001
linked-stories: []
linked-specs:
  - SPEC-003
  - SPEC-008
linked-bugs: []
linked-adrs:
  - ADR-008
  - ADR-006
depends-on:
  - ADR-008
---

# DESIGN-001: Porthole CLI for Nebula

## Interaction Surface

The `porthole` CLI — 12 commands for managing a personal Nebula overlay network. Covers network initialization, peer enrollment, config rendering, lighthouse provisioning, and fleet status.

**Scope:** The CLI command set, its arguments, output, and the state it manages. Not the TUI (DESIGN-002), not system internals (Spec), not hub infrastructure (SPEC-008).

## Architecture Overview

Porthole manages a Nebula overlay network using an offline certificate authority model. The operator's workstation holds a CA keypair (encrypted at rest with SOPS/age). Adding a peer means signing a certificate locally — no hub interaction required. The lighthouse (hub node) discovers peers automatically when they present valid certificates.

```
                        ┌─────────────────────┐
                        │    Lighthouse (hub)  │
                        │  nebula + CoreDNS +  │
                        │  Guacamole           │
                        │  10.100.0.1          │
                        └──────┬──────┬────────┘
                        UDP hole-punch / relay
                   ┌───────────┘      └───────────┐
            ┌──────┴──────┐              ┌────────┴─────┐
            │ workstation │              │    server    │
            │ 10.100.0.N  │──── p2p ────│  10.100.0.M  │
            └─────────────┘              └──────────────┘
```

**Trust model:** The CA private key never leaves the operator's workstation. Peers authenticate by presenting a CA-signed certificate. The lighthouse does not need to know about peers in advance — it validates certificates on connection and facilitates UDP hole-punching for direct peer-to-peer tunnels.

## CLI Commands

### Command reference

| Command | Arguments | Purpose | External tools |
|---------|-----------|---------|----------------|
| `porthole init` | `--endpoint`, `--age-key`, `--domain` | Create CA keypair, sign lighthouse certificate, initialize encrypted network state | `nebula-cert ca`, `nebula-cert sign`, `sops` |
| `porthole add` | `name`, `--role`, `--platform`, `--dns-name`, `--groups` | Allocate IP, sign peer certificate, add to state | `nebula-cert sign` |
| `porthole remove` | `name` | Remove peer from state, add cert fingerprint to blocklist | — |
| `porthole list` | `--json` | Display all peers with name, IP, groups, role, platform | — |
| `porthole peer-config` | `name`, `--out` | Render Nebula config bundle for a peer | Jinja2 |
| `porthole gen-peer-scripts` | `name`, `--out` | Generate platform-appropriate service files | Jinja2 |
| `porthole install-peer` | `name`, `--host` | SCP config bundle to peer, enable nebula service | `scp`, `ssh` |
| `porthole enroll` | `name`, `--manual` | Transfer config bundle to a peer via Magic Wormhole (or `--manual` for file path output) | `wormhole` |
| `porthole bootstrap` | `hub_host` | Provision lighthouse on a VPS via Terraform + Ansible | `terraform`, `ansible-playbook` |
| `porthole status` | — | Show live peer status from lighthouse | `ssh` |
| `porthole dashboard` | `--port` | Run local web dashboard showing fleet status | — |
| `porthole seed-guac` | `--out`, `--apply` | Generate Guacamole connection seed SQL from peer state | — |

### Command details

#### `porthole init`

Creates the network's root of trust and initial state file.

1. Generate CA keypair: `nebula-cert ca -name "porthole-ca" -duration <cert_duration>`
2. Sign lighthouse certificate: `nebula-cert sign -name "lighthouse" -ip "10.100.0.1/24" -groups "lighthouse" -ca-crt <ca.crt> -ca-key <ca.key>`
3. Write `network.sops.yaml` containing CA cert/key, lighthouse cert/key, and network config
4. Encrypt sensitive fields with SOPS (age key)

#### `porthole add`

Enrolls a new peer in the network. The operator runs this on their workstation — no hub interaction needed.

1. Decrypt `network.sops.yaml` to access CA key
2. Allocate next available IP from the subnet pool
3. Sign peer certificate: `nebula-cert sign -name "<name>" -ip "<ip>/24" -groups "<groups>" -ca-crt <ca.crt> -ca-key <ca.key>`
4. Append peer entry to state (cert, key, IP, role, platform, groups)
5. Re-encrypt and write state

The lighthouse discovers this peer when it connects — no config push or restart needed.

#### `porthole remove`

Removes a peer and revokes its certificate.

1. Remove peer entry from state
2. Add the peer's certificate fingerprint to the blocklist
3. Re-encrypt and write state

Certificate revocation takes effect in two ways:
- **Immediate:** Run `porthole deploy-lighthouse` to push the updated blocklist to the lighthouse
- **Natural:** The peer's certificate expires at its configured duration (default 1 year)

#### `porthole enroll`

Transfers the config bundle to a target peer. Two modes:

- **Default (Magic Wormhole):** Generates a one-time wormhole code. The operator enters the code on the target peer to receive `ca.crt`, `<name>.crt`, `<name>.key`, and `config.yml`.
- **`--manual`:** Writes the config bundle to a local directory and outputs the path for manual transfer (USB, SCP, etc.).

#### `porthole bootstrap`

Provisions the lighthouse on a fresh VPS:

1. `terraform apply` — creates the VPS, configures DNS, opens UDP port
2. `ansible-playbook` — installs and configures:
   - Nebula lighthouse (binary + config + CA cert + lighthouse cert/key)
   - CoreDNS (`.wg` domain resolution for peers)
   - Guacamole (Docker stack for browser-based remote desktop)

Cloud-init injects the lighthouse config at first boot. Nebula's built-in firewall handles access control (no separate firewall tooling).

#### `porthole status`

Queries the lighthouse for live peer status via SSH → nebula admin API.

Displayed fields: peer name, overlay IP, certificate groups, last handshake time, relay status, connection type (direct/relayed).

## State Schema

### `network.sops.yaml`

The single source of truth for the network, stored in the repo and encrypted with SOPS/age.

```yaml
# Certificate Authority
ca:
  cert: |
    -----BEGIN NEBULA CERTIFICATE-----
    ...
    -----END NEBULA CERTIFICATE-----
  key: |                              # SOPS-encrypted
    -----BEGIN NEBULA ED25519 PRIVATE KEY-----
    ...
    -----END NEBULA ED25519 PRIVATE KEY-----

# Network configuration
network:
  subnet: "10.100.0.0/24"
  domain: "wg"                        # CoreDNS zone (.wg)
  lighthouse_port: 4242               # Nebula UDP listen port
  cert_duration: "8760h"              # Default cert validity (1 year)

# Lighthouse (hub node)
lighthouse:
  name: "lighthouse"
  endpoint: "hub.example.com"
  ip: "10.100.0.1"
  cert: |
    -----BEGIN NEBULA CERTIFICATE-----
    ...
    -----END NEBULA CERTIFICATE-----
  key: |                              # SOPS-encrypted
    -----BEGIN NEBULA ED25519 PRIVATE KEY-----
    ...
    -----END NEBULA ED25519 PRIVATE KEY-----
  groups:
    - lighthouse

# Enrolled peers
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
    key: |                            # SOPS-encrypted
      -----BEGIN NEBULA ED25519 PRIVATE KEY-----
      ...
      -----END NEBULA ED25519 PRIVATE KEY-----
    reverse_ssh_port: 2202            # Fallback recovery (SPIKE-006)

# Guacamole
guacamole:
  admin_password: "..."               # SOPS-encrypted

# Certificate blocklist (revoked peers)
blocklist: []                         # Cert fingerprints
```

### Key schema concepts

- **CA cert + key** — the root of trust. The CA key is only decrypted on the operator's workstation during `porthole add` / `porthole init`. It is never deployed to any peer or the lighthouse.
- **Peer identity = CA-signed certificate** — each peer's cert encodes its name, overlay IP, and group memberships. The lighthouse validates certs on connection.
- **Groups** — map directly to roles (workstation, server, family, lighthouse). Used by Nebula's firewall rules for access control.
- **Blocklist** — certificate fingerprints of revoked peers. Deployed to the lighthouse config for immediate revocation.
- **Cert duration** — configurable expiry provides natural credential rotation. A future `porthole renew` command could re-sign expiring certs; for MVP, `porthole add --force` re-signs an existing peer's cert.

## Nebula Config Templates

### Lighthouse config (`lighthouse-config.yml.j2`)

Rendered during `porthole bootstrap` and deployed to the hub.

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
    # Guacamole web UI
    - port: 443
      proto: tcp
      groups:
        - workstation
        - server
```

### Peer config (`peer-config.yml.j2`)

Rendered by `porthole peer-config` and included in the enrollment bundle.

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
  port: 0                              # Random port — peers are not lighthouses

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

### Firewall model

Nebula's built-in firewall uses certificate groups for access control. Rules are defined in the config template and deployed with the lighthouse/peer config. No separate firewall tooling is needed.

Group-to-role mapping:
| Group | Members | Access |
|-------|---------|--------|
| `lighthouse` | Hub node | SSH from all groups, ICMP |
| `workstation` | Operator machines | SSH, RDP (3389), VNC (5900), Guacamole (443) |
| `server` | Headless nodes | SSH, Guacamole (443) |
| `family` | Non-technical users | ICMP only (managed via Guacamole) |

## Edge Cases and Error States

### CA key not available
If `network.sops.yaml` can't be decrypted (age key missing), `porthole add` fails with: "Cannot sign certificate — age key required to decrypt CA key. Run `porthole-setup` to configure secrets."

### Lighthouse unreachable after init
The lighthouse must be provisioned before peers can connect. If a peer is added but the lighthouse isn't running, the peer's nebula service retries connection in the background.

### Certificate expiry
Certs have a configurable duration (default 1 year). For MVP, `porthole add --force` re-signs an existing peer's cert. A future `porthole renew` command could automate bulk re-signing.

### Peer revocation
`porthole remove` adds the peer's cert fingerprint to the blocklist in state. For immediate effect, deploy the updated lighthouse config via Ansible (`porthole deploy-lighthouse`). Without deployment, the peer's certificate expires naturally.

### Platform-specific paths

| Platform | Binary | Config dir | Service |
|----------|--------|-----------|---------|
| Linux | `/usr/local/bin/nebula` | `/etc/nebula/` | systemd unit |
| macOS | `/usr/local/bin/nebula` | `/etc/nebula/` | launchd plist |
| Windows | `C:\Program Files\Nebula\nebula.exe` | `C:\Program Files\Nebula\` | `nebula.exe service install` |

## Design Decisions

1. **Offline CA model.** The CA private key lives only on the operator's workstation, encrypted with SOPS/age. Peer enrollment is a local `nebula-cert sign` — no network access to the lighthouse required. This means peers can be added from anywhere, even offline.

2. **Certificate groups as access control.** Roles (workstation, server, family, lighthouse) map directly to Nebula certificate groups. The lighthouse firewall config uses these groups for inbound rules. Access control is defined once in the config template and deployed with the lighthouse — no per-peer firewall management.

3. **Blocklist + expiry for revocation.** Two revocation mechanisms: the blocklist provides immediate revocation (requires lighthouse config redeploy), and certificate expiry provides natural credential rotation. Both are passive from the peer's perspective — no client-side action needed.

4. **Magic Wormhole for enrollment.** `porthole enroll` uses Magic Wormhole for zero-config transfer of the cert bundle to target peers. The operator runs `enroll` on their workstation and reads a code to the person at the target machine. `--manual` mode is available for air-gapped or scripted scenarios.

5. **Single service per node.** The `nebula` binary handles tunneling, reconnection (`punchy`), and relay fallback in a single process. One systemd/launchd unit per node. The optional SSH tunnel service (for reverse access fallback per SPIKE-006) is an add-on, not a default.

6. **State-in-repo.** `network.sops.yaml` lives in the git repo, encrypted. This gives versioned, auditable network state with no external database. The repo is the single source of truth — `porthole` commands read and write this file.

## Assets

| File | Description |
|------|-------------|
| [cli-command-map.md](./cli-command-map.md) | Detailed command-by-command reference with argument specifications and implementation notes |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-07 | — | Initial design |
