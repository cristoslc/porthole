# PRD-004: RustDesk Self-Hosted Relay

**Status:** Abandoned
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Research:** None (architecture is well-documented; no spike needed)
**ADR:** [(ADR-001) RustDesk for Remote Desktop](../../../adr/Adopted/(ADR-001)-RustDesk-for-Remote-Desktop.md), [(ADR-003) Network Layer for Remote Fleet](../../../adr/Proposed/(ADR-003)-Network-Layer-for-Remote-Fleet.md)
**Parent Epic:** [(EPIC-001) Remote Fleet Management](../../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Related:** [(SPEC-002) Remote Desktop Bootstrap](../../../spec/Implemented/(SPEC-002)-Remote-Desktop/(SPEC-002)-Remote-Desktop.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-02-28 | daa2035 | Initial creation |
| Abandoned | 2026-02-28 | 40abf39 | ADR-003 recommends Tailscale ACLs, eliminating the need for a self-hosted relay. RustDesk architecture background retained as reference. |

---

## Background: How RustDesk Works

RustDesk is an open-source remote desktop application whose architecture
separates **signaling** from **data transport**. Understanding the two-server
model and NAT traversal strategy is essential context for this PRD.

### Two-server architecture

RustDesk's server infrastructure consists of two cooperating processes:

```
                        Internet / LAN
                             |
              +--------------+--------------+
              |                             |
        +-----+------+              +------+------+
        |    hbbs     |              |    hbbr     |
        | Rendezvous  |              |   Relay     |
        |   Server    |              |   Server    |
        +------+------+              +------+------+
               |                            |
   NAT punch   |   signaling / peer         |   fallback data
   coordination|   discovery                |   forwarding
               |                            |
        +------+----------------------------+------+
        |              |              |            |
     Client A       Client B      Client C     Client D
```

**hbbs (Rendezvous / ID Server)** — The control plane. Responsibilities:

- **Peer registration:** Each RustDesk client registers its 9-digit ID and
  current IP/port with hbbs over UDP (port 21116). This is how peers discover
  each other.
- **NAT traversal coordination:** When Client A wants to connect to Client B,
  it asks hbbs. The server brokers the introduction — exchanging each peer's
  public IP:port so they can attempt a direct connection via UDP hole-punching.
- **Relay assignment:** If hole-punching fails, hbbs tells the clients which
  hbbr relay server to use for the session.
- **TCP signaling:** Persistent TCP connections (port 21115) carry the
  signaling channel for connection setup, heartbeats, and peer presence.
- **API server (Pro only):** Port 21114 provides a web console, address book
  sync, and device management REST API. Not present in the OSS server.

**hbbr (Relay Server)** — The data plane fallback. Responsibilities:

- **Traffic forwarding:** When two clients cannot establish a direct P2P
  connection, hbbr receives the encrypted stream from one peer and forwards it
  to the other. The relay is a dumb pipe — it cannot decrypt the session.
- **TCP transport:** Listens on port 21117 (native TCP) and optionally port
  21119 (WebSocket, for browser clients and restrictive networks).

Both processes are shipped in a single `rustdesk-server` binary/container and
are typically co-located on the same host.

### Port map

| Port  | Protocol | Process | Purpose |
|-------|----------|---------|---------|
| 21114 | TCP      | hbbs   | Web console + API (Pro only) |
| 21115 | TCP      | hbbs   | NAT type test / signaling |
| 21116 | TCP+UDP  | hbbs   | ID registration (UDP), hole-punch relay (TCP) |
| 21117 | TCP      | hbbr   | Relay sessions |
| 21118 | TCP      | hbbs   | WebSocket signaling (browser clients) |
| 21119 | TCP      | hbbr   | WebSocket relay (browser clients) |

### NAT traversal and relay fallback

RustDesk's connection strategy follows a preference cascade:

1. **Direct LAN connection** — If both peers are on the same local network,
   they connect directly. No server involvement beyond initial peer lookup.
2. **UDP hole-punching** — hbbs determines each peer's NAT type using STUN-like
   probing (port 21116 UDP). If both peers are behind "cone" NATs
   (Full Cone, Restricted Cone, or Port-Restricted Cone), hbbs exchanges their
   public IP:port mappings and both peers send UDP packets to open pinholes in
   their NATs. This usually succeeds in under a second.
3. **TCP hole-punching** — Attempted if UDP hole-punching fails (e.g., one peer
   is behind a symmetric NAT). Less reliable than UDP hole-punching.
4. **Relay via hbbr** — The last resort. If all hole-punching attempts fail
   (typically when both peers are behind symmetric NATs, or aggressive firewalls
   block UDP), traffic is forwarded through the relay server. The relay adds
   latency (two hops instead of zero) and consumes server bandwidth, but
   guarantees connectivity.

In practice, hole-punching succeeds for the majority of residential and small
business networks. Relay is primarily needed for corporate firewalls, CGNAT
(carrier-grade NAT), and symmetric NAT routers.

### Encryption and security model

RustDesk uses end-to-end encryption for all sessions:

- **Key pair:** When hbbs starts for the first time, it generates an
  Ed25519/X25519 key pair (`id_ed25519` and `id_ed25519.pub`). The public key
  is embedded in every client that connects to this server — clients use it to
  verify the server's identity and establish a secure channel.
- **Session encryption:** Each remote desktop session negotiates a per-session
  key using the server's key pair for initial authentication, then encrypts the
  video/input stream. The relay server (hbbr) sees only ciphertext — it
  cannot inspect or tamper with session content.
- **Client key distribution:** The server's public key must be configured on
  each client. This can be done via the client UI (ID Server + Key fields),
  command-line flags, a custom client build with the key baked in, or
  group policy / MDM on managed networks.
- **No account required (OSS):** The OSS server has no user authentication,
  address book, or access control. Anyone who knows a machine's RustDesk ID
  and has the connection password can connect. The Pro server adds OIDC/LDAP
  authentication, device groups, and access policies.

### Default public infrastructure vs. self-hosted

RustDesk operates free public rendezvous/relay servers for users who don't
self-host. The limitations of the public servers motivate self-hosting:

| Concern | Public servers | Self-hosted |
|---------|---------------|-------------|
| **Privacy** | Peer IPs and connection metadata flow through third-party servers | All traffic stays on your infrastructure |
| **Reliability** | Shared capacity, variable load, no SLA | Dedicated resources, sized to your fleet |
| **Latency** | Servers in limited regions; relay adds geographic round-trips | Place the relay near your machines for minimum latency |
| **Bandwidth** | Speed caps on relayed connections | No artificial limits |
| **Availability** | Public servers have experienced outages and congestion | You control uptime and maintenance windows |
| **Key control** | Default keys are shared across all public server users | Your own key pair — only your clients trust your server |
| **Compliance** | Third-party data processing | Data sovereignty |

---

## Problem

PRD-002 (Remote Desktop Bootstrap) deployed RustDesk on all workstations but
explicitly deferred relay server deployment as out of scope:

> *"Deploying a RustDesk relay server (that's infrastructure, not workstation
> provisioning)"* — PRD-002, Out of scope

Today, RustDesk clients fall back to the public relay infrastructure when direct
P2P connections fail. This creates several problems:

1. **Privacy:** Connection metadata (peer IPs, connection times, durations)
   passes through third-party infrastructure. Even though session content is
   encrypted, the metadata itself reveals which machines are communicating
   and when.
2. **Reliability:** Public relay servers are shared resources with no SLA. Users
   have reported intermittent connectivity failures, congestion during peak
   times, and multi-hour outages.
3. **Latency:** Public relay servers may be geographically distant from both
   peers, adding 50-200ms of round-trip latency on relayed connections.
4. **Bandwidth caps:** Public relay connections may be speed-limited, making
   high-resolution remote desktop sessions sluggish.
5. **No key sovereignty:** Without a self-hosted server, clients either use the
   default public key (shared with all users) or must be manually configured
   per-machine. A self-hosted server gives a single trust anchor for the
   entire fleet.

## Goal

Deploy a self-hosted RustDesk rendezvous + relay server and configure all
managed workstations to use it, so that:

- All peer discovery and relay traffic stays on owned infrastructure.
- Connection reliability and latency are under our control.
- A single key pair provides fleet-wide identity verification.
- Public relay infrastructure is no longer a dependency.

## Scope

### In scope

- **RustDesk server deployment** — `hbbs` + `hbbr` running as a persistent
  service (Docker Compose or systemd) on a host accessible to all workstations.
- **Key pair generation and management** — Generate the Ed25519 key pair,
  distribute the public key to all clients, encrypt and store the private key
  in the repo.
- **Client configuration** — Update the `remote-desktop` Ansible role to
  configure RustDesk clients with the self-hosted server address and public
  key. After `make apply`, clients automatically point to the self-hosted
  relay.
- **Firewall / network configuration** — Document (and where possible
  automate) the required port openings on the server host.
- **DNS entry** — A DNS name for the relay server (e.g.,
  `rustdesk.example.com`) so clients are not hard-coded to an IP.
- **Monitoring and health checks** — Basic liveness check to verify hbbs/hbbr
  are running and reachable.
- **Documentation** — Post-install verification steps, troubleshooting guide,
  key rotation procedure.

### Out of scope

- **RustDesk Server Pro** — The OSS server is sufficient for a personal fleet.
  Web console, OIDC, address book sync, and device management are not needed.
- **High availability / clustering** — Single server instance is adequate for a
  personal fleet of < 10 machines. No load balancer or failover needed.
- **Custom client builds** — Embedding the server key into a custom-compiled
  RustDesk client. Ansible config templating achieves the same result without
  maintaining a fork.
- **Mobile clients** — Android/iOS RustDesk configuration is manual and outside
  the Ansible-managed fleet.
- **WebSocket-only mode** — Not needed for a personal fleet on Tailscale.
  Standard TCP ports are sufficient.

---

## Architecture

### Deployment topology

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  Relay Host (Proxmox VM / VPS / always-on machine)              │
 │                                                                  │
 │  ┌────────────────────────────────────────────────────────────┐  │
 │  │  Docker Compose (or systemd)                               │  │
 │  │                                                            │  │
 │  │  ┌──────────┐    ┌──────────┐    ┌─────────────────────┐  │  │
 │  │  │   hbbs   │    │   hbbr   │    │  data volume        │  │  │
 │  │  │ :21115   │    │ :21117   │    │  id_ed25519         │  │  │
 │  │  │ :21116   │    │ :21119   │    │  id_ed25519.pub     │  │  │
 │  │  │ :21118   │    │          │    │  db_v2.sqlite3      │  │  │
 │  │  └──────────┘    └──────────┘    └─────────────────────┘  │  │
 │  └────────────────────────────────────────────────────────────┘  │
 │                                                                  │
 │  Ports exposed: 21115-21119/tcp, 21116/udp                      │
 └──────────────────────────────────────────────────────────────────┘
          │
          │  Tailscale mesh / Internet
          │
    ┌─────┼──────────────────────────────────┐
    │     │              │                   │
 ┌──┴──┐  ┌──┴──┐  ┌──┴──┐            ┌──┴──┐
 │ Mac │  │ Lin │  │ Lin │   . . .    │ Mac │
 │ WS1 │  │ WS2 │  │ WS3 │            │ WSn │
 └─────┘  └─────┘  └─────┘            └─────┘
   ID server: rustdesk.example.com
   Key:       <public-key-string>
```

### Connection flow with self-hosted relay

1. **Registration:** Each workstation's RustDesk client registers its ID with
   hbbs at `rustdesk.example.com:21116` (UDP).
2. **Connection request:** When WS1 wants to connect to WS2, it sends a
   signaling request to hbbs (TCP :21115).
3. **Hole-punch attempt:** hbbs exchanges peer addresses. Both clients attempt
   direct P2P via UDP hole-punching.
4. **Relay fallback:** If hole-punching fails, hbbs directs both clients to
   hbbr at `rustdesk.example.com:21117`. The encrypted stream is forwarded
   through the relay.
5. **All traffic on owned infrastructure:** Whether direct or relayed, the
   signaling always goes through our hbbs. Relay traffic goes through our hbbr.
   Public servers are never contacted.

### Hosting options

| Option | Pros | Cons | Recommended |
|--------|------|------|-------------|
| **Proxmox LXC/VM** (on-prem) | Zero cost, lowest latency for LAN, full control | Not reachable from outside without Tailscale or port forwarding | Yes, if all machines are on Tailscale |
| **VPS** (e.g., Hetzner, Oracle Cloud free tier) | Reachable from anywhere, static public IP | Monthly cost (minimal — 1 vCPU/1 GB is sufficient), data leaves LAN for relay | Yes, for mixed local/remote fleet |
| **Always-on workstation** | No additional infra | Tied to one machine's uptime, conflicts with sleep/reboot | No |

For a personal fleet where all machines are on a Tailscale mesh, a **Proxmox
LXC container** is the simplest option: hbbs/hbbr are accessible via Tailscale
IPs, and no public port exposure or DNS is needed beyond Tailscale MagicDNS.

### Docker Compose deployment

```yaml
# docker-compose.yml
services:
  hbbs:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk-hbbs
    command: hbbs
    volumes:
      - ./data:/root
    network_mode: host
    restart: unless-stopped

  hbbr:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk-hbbr
    command: hbbr
    volumes:
      - ./data:/root
    network_mode: host
    restart: unless-stopped
```

`network_mode: host` is recommended because hbbs needs both TCP and UDP on the
same port (21116), which Docker's port mapping handles awkwardly. On first
start, hbbs generates the key pair in `./data/`.

### Resource requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| CPU | 1 vCPU | hbbs/hbbr are written in Rust, extremely efficient. Near-zero CPU at idle. |
| Memory | 512 MB (256 MB minimum) | hbbs ~5 MB RSS, hbbr ~3 MB RSS. The rest is OS overhead. |
| Disk | 1 GB | Key pair + SQLite DB. Negligible growth. |
| Bandwidth | Minimal for signaling; ~2-10 Mbps per relayed session | Most connections are P2P (no relay bandwidth). Budget for 1-2 concurrent relayed sessions max for a personal fleet. |

### Key management

| Artifact | Location | Encryption | Purpose |
|----------|----------|------------|---------|
| `id_ed25519` (private key) | Server `./data/` directory + encrypted backup in repo | age-encrypted in repo per AGENTS.md policy | Server identity — hbbs uses this for client authentication |
| `id_ed25519.pub` (public key) | Server `./data/` + Ansible role defaults | Not encrypted (public) | Distributed to all clients — clients verify the server's identity |
| Public key string | Ansible variable `rustdesk_relay_key` | Plaintext in role defaults | The base64 key string configured on each client |

The private key MUST NOT be committed to the repo in plaintext. Following the
encryption-at-rest policy (AGENTS.md), it is age-encrypted before committing.

### Client configuration (Ansible)

The existing `remote-desktop` role gains new variables and a configuration task:

```yaml
# shared/roles/remote-desktop/defaults/main.yml (additions)
rustdesk_id_server: ""          # e.g., "rustdesk.example.com" or Tailscale IP
rustdesk_relay_server: ""       # usually same as id_server; can differ
rustdesk_api_server: ""         # empty for OSS server (no API)
rustdesk_key: ""                # public key string from id_ed25519.pub
```

**Linux configuration:** RustDesk reads its config from
`/root/.config/rustdesk/RustDesk2.toml` (system-wide) or
`~/.config/rustdesk/RustDesk2.toml` (per-user). Ansible templates the relevant
fields:

```toml
[options]
custom-rendezvous-server = "rustdesk.example.com"
relay-server = "rustdesk.example.com"
key = "<public-key-string>"
```

**macOS configuration:** RustDesk on macOS stores configuration in
`~/Library/Preferences/com.carriez.RustDesk/RustDesk2.toml` with the same
format.

---

## Deliverables

### D1: Server deployment artifacts

New directory: `infra/rustdesk-relay/` (or appropriate location for
infrastructure-as-code).

- `docker-compose.yml` — hbbs + hbbr as described in the Architecture section.
- `README.md` — Setup instructions: first-time key generation, starting the
  service, verifying connectivity.
- Ansible playbook or manual runbook for deploying to the target host
  (Proxmox LXC, VPS, etc.).

### D2: Key pair generation and secure storage

- Generate key pair on first server start (automatic with hbbs).
- Copy `id_ed25519.pub` content to `rustdesk_key` Ansible variable.
- Age-encrypt `id_ed25519` private key and store in repo (following
  encryption-at-rest policy).
- Document key rotation procedure (generate new pair, redistribute public key
  to all clients, restart server).

### D3: Client configuration update

Update `shared/roles/remote-desktop/` to configure RustDesk clients:

- Add `rustdesk_id_server`, `rustdesk_relay_server`, and `rustdesk_key`
  to role defaults.
- New task: template `RustDesk2.toml` with the server address and key on both
  platforms.
- Idempotent: only updates config if values differ from current state.
- Tags: `rustdesk`, `rustdesk-config`.

### D4: Network / firewall documentation

Document the required port openings for the relay host:

- Ports 21115-21119 TCP + 21116 UDP.
- If using Tailscale: no firewall changes needed (Tailscale handles routing).
- If exposing to the internet: firewall rules, fail2ban considerations, and
  the recommendation to restrict source IPs if possible.

### D5: DNS configuration

- Create a DNS record (A or CNAME) pointing to the relay server.
- If using Tailscale MagicDNS only, document the MagicDNS hostname.
- Ansible variable references DNS name, not bare IP.

### D6: Health monitoring

- Basic health check: TCP connect to hbbs port 21116 and hbbr port 21117.
- Optional: cron/timer that tests connectivity and alerts on failure (can
  reuse the notification infrastructure from PRD-002's backup stack pattern
  — desktop notification + SMTP email).
- Document manual verification: `telnet rustdesk.example.com 21116`.

### D7: Post-install and troubleshooting docs

Update `docs/post-install.md`:

- Verify RustDesk connects to self-hosted server (Settings > ID/Relay Server
  should show the configured address).
- Test a connection between two machines.
- Troubleshooting: common issues (port blocked, key mismatch, DNS not
  resolving, hbbs/hbbr not running).

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Relay host goes down | All relayed connections fail; direct P2P connections continue to work | Run on stable infrastructure (Proxmox VM with auto-restart, or VPS with SLA). Health monitoring (D6) alerts on failure. Clients can temporarily fall back to public servers by clearing config. |
| Key mismatch between server and clients | Clients silently fail to connect — no clear error message | Ansible ensures all clients get the same key from a single variable. Include key verification in post-install checks (D7). |
| Relay host IP changes | Clients can't find the server | Use DNS name (D5), not bare IP. Update DNS record if IP changes. MagicDNS handles this automatically for Tailscale. |
| hbbr memory leak (known issue #438) | Relay process crashes after extended uptime | Docker `restart: unless-stopped` auto-recovers. Monitor memory usage. Update when upstream fixes land. |
| Port 21116 UDP blocked by network | Hole-punching fails, all connections go through relay | This is the expected fallback — relay handles it. Document that UDP 21116 should be open for optimal performance. |
| Private key compromised | Attacker could impersonate the server (MITM) | Age-encrypt private key in repo. Rotate key pair: generate new on server, update Ansible variable, `make apply` to push new key to all clients. |
| OSS server lacks access control | Anyone who discovers the server can use it for relay | Restrict network access (Tailscale ACLs or firewall source-IP rules). Acceptable risk for a personal fleet. |
| RustDesk config file location changes in a future version | Ansible config templating breaks | Pin RustDesk version in the role. Test config path before templating. |

---

## Implementation approach

```
Phase 1: Server deployment
  D1: Docker Compose + deployment to target host
  D2: Key pair generation, public key extraction, private key encryption

Phase 2: Client configuration
  D3: Ansible role update — template RustDesk config with server + key
  D5: DNS entry (or Tailscale MagicDNS documentation)

Phase 3: Documentation and monitoring
  D4: Firewall / port documentation
  D6: Health check setup
  D7: Post-install and troubleshooting docs

Phase 4: Verification
  - Verify hbbs/hbbr are running and reachable from all workstations
  - Verify RustDesk clients show the self-hosted server in Settings
  - Test direct P2P connection between two LAN machines
  - Test relayed connection (simulate by blocking UDP 21116 on one peer)
  - Verify key mismatch is detected (intentionally use wrong key)
  - Verify server auto-restarts after simulated crash
```

---

## Success criteria

1. `hbbs` and `hbbr` are running on the designated host and survive reboot.
2. `make apply ROLE=remote-desktop` configures all workstations to use the
   self-hosted server — no manual client configuration.
3. RustDesk Settings on each client shows the correct ID Server and Key.
4. Two workstations can establish a remote desktop session routed entirely
   through the self-hosted infrastructure (verified by checking connection
   info in RustDesk — should show the self-hosted server, not public).
5. Relayed connections work when hole-punching is blocked.
6. The server's private key is age-encrypted in the repo — no plaintext
   secrets in git.
7. Health monitoring alerts within 5 minutes if hbbs or hbbr goes down.
8. Post-install documentation covers verification and common troubleshooting
   steps.
