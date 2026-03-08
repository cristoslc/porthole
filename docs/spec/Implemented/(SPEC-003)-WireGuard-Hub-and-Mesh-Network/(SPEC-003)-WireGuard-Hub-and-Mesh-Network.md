---
artifact: SPEC-003
title: WireGuard Hub & Mesh Network
status: Implemented
author: cristos
created: 2026-03-03
last-updated: 2026-03-04
parent-epic: EPIC-001
linked-research:
  - SPIKE-007
linked-adrs:
  - ADR-004
  - ADR-008
depends-on: []
addresses:
  - JOURNEY-003.PP-01
  - JOURNEY-003.PP-05
---

# SPEC-003: WireGuard Hub & Mesh Network

**Status:** Implemented
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [(EPIC-001) Remote Fleet Management](../../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Research:** [(SPIKE-007) Ephemeral VPS Hub Feasibility](../../../research/Complete/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility.md)
**ADR:** [(ADR-004) WireGuard Hub-and-Spoke Relay](../../../adr/Superseded/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) (Superseded by [ADR-008](../../../adr/Adopted/(ADR-008)-Nebula-Overlay-Network.md))

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-03 | 6297014 | Initial creation |
| Implemented | 2026-03-03 | d46e0d2 | porthole CLI (EPIC-002) implements all templates, state schema, subnet/key/sops/state/render/ssh modules |

---

## Problem Statement

The fleet has no private network layer. Machines are scattered across
residential NATs, carrier-grade NATs, and hotel WiFi. There is no way to
reach one machine from another without manual per-machine VPN configuration,
dynamic DNS hacks, or reliance on a third-party overlay network (Tailscale,
ZeroTier). Each new machine means repeating the setup. Each network change
risks breaking connectivity.

ADR-004 adopted a self-hosted WireGuard hub-and-spoke relay via VPS. This
spec defines the **target state** of that network — what the hub looks like,
how peers are configured, how DNS works — so it can be stood up manually and
validated before any automation tooling exists.

## External Behavior

After this spec is implemented, the operator can:

1. Provision a VPS and apply hub configuration (WireGuard, nftables, CoreDNS)
   from rendered templates.
2. Enroll a new peer by generating keys, assigning an IP, rendering a config,
   and transferring it to the target machine.
3. Resolve any peer by hostname via `hostname.wg` DNS from within the mesh.
4. Route traffic between any two peers through the hub.
5. Rebuild the entire network from the repo on a fresh VPS in under 10
   minutes.

## Acceptance Criteria

1. A freshly provisioned VPS running the hub config accepts WireGuard
   connections from enrolled peers and forwards inter-peer traffic.
2. `nslookup hostname.wg 10.100.0.1` returns the correct WireGuard IP for
   every enrolled peer.
3. Two peers on different networks can `ping` each other through the hub.
4. Two peers on different networks can establish an SSH session via
   `ssh hostname.wg`.
5. Hub firewall (nftables) allows only WireGuard (UDP 51820), SSH (TCP 22
   from operator IP or WireGuard subnet), and DNS (TCP/UDP 53 on WireGuard
   interface). All other inbound traffic is dropped.
6. `network.sops.yaml` round-trips correctly: decrypt, render templates,
   deploy, verify connectivity.
7. Adding a new peer (key gen, IP assign, state file update, template render)
   can be completed manually in under 5 minutes.
8. The hub can be destroyed and rebuilt from repo state with connectivity
   restored within 10 minutes.

## Scope & Constraints

### In scope

- **Hub WireGuard server configuration**: `wg0.conf` with all peer stanzas,
  IP forwarding (`sysctl net.ipv4.ip_forward=1`), `PostUp`/`PostDown` rules.
- **Hub firewall (nftables)**: Restrictive inbound rules — WireGuard, SSH,
  DNS on WireGuard interface only. Forward chain allows inter-peer traffic.
- **`network.sops.yaml` schema**: Canonical structure for defining peers,
  including: peer name, WireGuard public key, WireGuard private key
  (encrypted), assigned IP, DNS name, role (hub/workstation/server/family),
  platform (linux/macos/windows — optional, used by `seed-guac` to select
  the correct remote desktop protocol), reverse SSH port (2200+N), and
  optional metadata. See updated schema below.
- **Jinja2 templates**:
  - `templates/hub-wg0.conf.j2` — hub WireGuard config with all peer stanzas
  - `templates/peer-wg0.conf.j2` — individual peer WireGuard config
  - `templates/coredns-wg.zone.j2` — CoreDNS zone file for `.wg` domain
  - `templates/nftables.conf.j2` — hub firewall rules
- **CoreDNS `.wg` zone**: DNS server on the hub listening on the WireGuard
  interface (10.100.0.1). Zone file generated from `network.sops.yaml`.
  Resolves `hostname.wg` to WireGuard IPs for all peers.
- **Subnet allocation**: `10.100.0.0/24`. Hub at `10.100.0.1`. Peers
  assigned sequentially from `10.100.0.2`.
- **DNS endpoint strategy**: Peers connect to `hub.yourdomain.com:51820`.
  Cloudflare A record points to VPS public IP. `reresolve-dns.sh` on peers
  handles hub IP changes (provider migration, ephemeral VPS recreation).
- **Peer enrollment procedure**: Manual workflow — install WireGuard on the
  target machine (per-OS), generate key pair, assign next available IP, update
  `network.sops.yaml`, render templates, transfer peer config via Magic
  Wormhole, enable and start the WireGuard service.
- **SOPS/age encryption**: All private keys encrypted in repo. Age key on
  operator workstation and VPS only.

### Porthole CLI extensions (gap fills)

The following CLI commands extend the base porthole CLI to address gaps
identified in JOURNEY-002 and JOURNEY-003:

**`porthole add <name> --role <role> --platform <platform>`**
- Adds `--platform` flag to the existing `add` command.
- Stores the platform in the peer record in `network.sops.yaml`.
- Valid values: `linux` (default), `macos`, `windows`.

**`porthole peer-config <name>`**
- Outputs the decrypted `wg0.conf` for a single named peer to stdout (or
  `--out <file>`).
- Prints a warning that the file contains the peer's WireGuard private key
  in plaintext and recommends deleting it after transfer.
- Addresses JOURNEY-003.PP-01: provides a dedicated command for extracting
  the peer config needed for Windows enrollment without the full
  `gen-peer-scripts` bundle.

**`porthole install-peer <name>`**
- Installs generated peer scripts (from `gen-peer-scripts`) into system
  directories and enables services. Platform-aware:
  - **Linux**: copies watchdog/tunnel/status scripts to `/usr/local/bin/`,
    copies systemd units to `/etc/systemd/system/`, runs `daemon-reload`,
    enables and starts each unit.
  - **macOS**: copies plists to `/Library/LaunchDaemons/`, runs
    `launchctl load -w` for each.
- Requires sudo / elevated permissions.
- Idempotent: re-running on an already-installed peer re-copies and
  re-enables without error.
- Addresses JOURNEY-002.PP-04.

### Out of scope

- **Automation tooling**: The `porthole` CLI (EPIC-002) automates this spec's
  manual procedures. This spec defines the target state, not the tooling.
- **VPS provisioning**: Terraform modules and cloud-init (EPIC-005) provision
  the VPS to this spec's target state. This spec assumes a running VPS.
- **Guacamole or remote desktop**: Covered by SPEC-004.
- **Health monitoring and recovery**: Covered by SPEC-005.
- **Homelab service exposure**: DNS for `home.example.com` and reverse proxy
  belong to EPIC-006. The `.wg` zone is mesh-only infrastructure.

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| ADR-004 | Decision | WireGuard hub-and-spoke is the adopted network model |
| SPIKE-007 | Research | Ephemeral hub feasibility, DNS endpoint strategy, rebuild times |
| VPS with public IP | Infrastructure | Any provider, any region; ~$3-6/mo |
| Cloudflare DNS | Service | A record management for hub endpoint |
| SOPS + age | Tooling | Secret encryption for `network.sops.yaml` |
| WireGuard on peers | Software | Linux: `apt install wireguard` (kernel module built-in 5.6+); macOS: `brew install wireguard-tools`; Windows: official MSI installer |

## Design

### Network topology

```
                    Internet
                       |
              +--------+--------+
              |   VPS Hub       |
              |  10.100.0.1     |
              |  WireGuard +    |
              |  CoreDNS +      |
              |  nftables       |
              +---+----+----+---+
                  |    |    |
         +--------+  +--+  +--------+
         |           |           |
   +-----+-----+ +--+------+ +-+-------+
   | Peer A     | | Peer B  | | Peer C  |
   | 10.100.0.2 | | .0.3    | | .0.4    |
   | Linux WS   | | macOS   | | Windows |
   +------------+ +---------+ +---------+
```

### State file schema (`network.sops.yaml`)

```yaml
network:
  domain: wg
  subnet: 10.100.0.0/24
  hub:
    endpoint: hub.yourdomain.com:51820
    public_ip: <VPS public IP>  # cleartext
  peers:
    - name: hub
      ip: 10.100.0.1
      public_key: <cleartext>
      private_key: <SOPS-encrypted>
      dns_name: hub
      role: hub
    - name: desktop-linux
      ip: 10.100.0.2
      public_key: <cleartext>
      private_key: <SOPS-encrypted>
      dns_name: desktop-linux
      role: workstation
      reverse_ssh_port: 2202
    - name: mom-imac
      ip: 10.100.0.10
      public_key: <cleartext>
      private_key: <SOPS-encrypted>
      dns_name: mom-imac
      role: family
      platform: macos        # optional: linux | macos | windows
      reverse_ssh_port: 2210
    - name: dad-pc
      ip: 10.100.0.11
      public_key: <cleartext>
      private_key: <SOPS-encrypted>
      dns_name: dad-pc
      role: family
      platform: windows      # controls RDP vs VNC vs xrdp in seed-guac
      reverse_ssh_port: 2211
```

**`platform` field** (optional):

| Value | Default behavior in `seed-guac` |
|-------|----------------------------------|
| `linux` | xrdp (RDP on port 3389) + SSH |
| `macos` | VNC / Screen Sharing (port 5900) + SSH |
| `windows` | RDP (port 3389) + SSH |
| *(absent)* | Inferred from peer `name` if it contains "windows" or "mac"; otherwise defaults to `linux` — **unreliable, use explicit field** |

The `platform` field is set once at enrollment (`porthole add <name> --platform <value>`)
and stored in `network.sops.yaml`. It is not a secret and is not SOPS-encrypted.

### CoreDNS configuration

CoreDNS listens on `10.100.0.1:53` (WireGuard interface only). The `.wg`
zone is a static file generated from `network.sops.yaml`:

```
$ORIGIN wg.
@       IN SOA  hub.wg. admin.wg. ( 2026030301 3600 900 604800 86400 )
hub             IN A    10.100.0.1
desktop-linux   IN A    10.100.0.2
mom-imac        IN A    10.100.0.10
```

Upstream DNS (Cloudflare 1.1.1.1) handles all non-`.wg` queries.

### Peer WireGuard installation

WireGuard must be installed on each peer before enrollment. The steps vary
by OS:

**Linux (Ubuntu/Debian):**
```bash
sudo apt install wireguard wireguard-tools
# Kernel module is built-in on Linux 5.6+; older kernels need wireguard-dkms
```

**macOS:**
```bash
brew install wireguard-tools
# Uses userspace Go implementation; no kernel module needed
```

**Windows:**
- Download and run the official MSI installer from
  [wireguard.com/install](https://www.wireguard.com/install/)
- Installs both the tunnel service and `wg.exe` / `wg-quick.exe` CLI tools

After installation, verify with `wg --version`. The WireGuard interface
(`wg0`) is created when `wg-quick up` is run with the peer's rendered config.

### DNS endpoint and `reresolve-dns.sh`

Peer configs use `Endpoint = hub.yourdomain.com:51820` instead of a bare IP.
A cron job / systemd timer on each peer runs `reresolve-dns.sh` every 30
seconds, re-resolving the endpoint hostname and updating the WireGuard
endpoint if the IP has changed. This enables:

- Provider migration (move VPS to a different provider, update Cloudflare A
  record, peers reconnect automatically).
- Ephemeral hub recreation (destroy and recreate VPS, peers reconnect within
  ~2-3 minutes via DNS + PersistentKeepalive).

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| VPS provider outage | All inter-peer connectivity lost | Reverse SSH fallback (SPEC-005 Layer 2); ephemeral model allows rapid provider switch |
| SOPS key compromise | All WireGuard private keys exposed | Age key stored only on operator workstation and VPS; rotate keys via `porthole` when available |
| DNS propagation delay | Peers cannot reconnect after hub IP change | Low TTL (60s) on Cloudflare A record; `reresolve-dns.sh` polls every 30s |
| Subnet exhaustion (10.100.0.0/24) | Cannot add more than ~253 peers | Fleet is ~10 machines; /24 is sufficient for foreseeable scale |
| CoreDNS misconfiguration | Hostname resolution fails within mesh | Zone file is generated from state file; acceptance test validates resolution |
