---
title: "Nebula Overlay Network"
artifact: ADR-008
status: Adopted
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
supersedes: ADR-004
linked-epics:
  - EPIC-001
  - EPIC-007
linked-specs: []
linked-research:
  - SPIKE-009
depends-on: []
---

# ADR-008: Nebula Overlay Network

**Status:** Adopted
**Author:** cristos
**Created:** 2026-03-07
**Last Updated:** 2026-03-07
**Supersedes:** [ADR-004 — WireGuard Hub-and-Spoke Relay](../Superseded/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md)
**Renders unnecessary:** [ADR-007 — Age-Encrypted Setup Key and Cloud-Init Bootstrap](../Abandoned/(ADR-007)-Age-Encrypted-Setup-Key-and-Cloud-Init-Bootstrap.md)
**Informed by:** [SPIKE-009 — WireGuard Bootstrap Without SSH](../../research/Active/(SPIKE-009)-WireGuard-Bootstrap-Without-SSH/(SPIKE-009)-WireGuard-Bootstrap-Without-SSH.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-03-07 | — | Based on SPIKE-009 WireGuard vs Nebula comparison |

---

## Context

ADR-004 adopted a self-hosted WireGuard hub-and-spoke relay for the fleet overlay network. During pre-deployment research (SPIKE-009), a fundamental limitation surfaced: the **spoke N+1 problem**.

Adding a new peer to a WireGuard network requires updating the hub's `wg0.conf` with the new peer's public key and AllowedIPs, then reloading the service. This requires a management channel (SSH) to the hub — but the new spoke isn't on the WireGuard network yet, so it can't reach the hub over the tunnel. The options are:

1. SSH over the public internet (security exposure ADR-007 tried to mitigate)
2. SSH from an existing spoke (only works if provisioning workstation is already enrolled)
3. A coordination server (Headscale, Netmaker — adds infrastructure and lock-in)
4. An HTTPS enrollment API on the hub (custom code to build and maintain)

ADR-007 proposed an age-encrypted setup-only SSH key with cloud-init to minimize this exposure. While workable, it adds a third credential domain and a temporary-SSH-window dance (`hub-ssh-open` / `hub-ssh-close`) that is fundamentally a workaround for WireGuard's architectural limitation.

**Nothing is deployed yet.** The provisioning CLI, Terraform modules, and cloud-init templates exist in code but have not been used in production. Switching the tunnel layer now is greenfield work, not a migration.

## Decision

**Adopt Nebula as the overlay network layer, replacing WireGuard.**

Nebula (MIT license, slackhq/nebula, 17.1k GitHub stars) is a certificate-based overlay network created by Slack, running on 50,000+ production hosts. It uses the Noise Protocol Framework with AES-256-GCM encryption.

### Why Nebula over WireGuard

**1. Spoke N+1 is solved architecturally.** Nebula uses a Certificate Authority model. To enroll a new peer:
- The operator signs a certificate offline: `nebula-cert sign -name "new-spoke" -ip "10.100.0.5/24" -groups "workstation"`
- The signed cert + nebula config are distributed to the new node
- The node starts nebula, contacts the lighthouse, and is discovered automatically
- **No lighthouse config change. No SSH. No coordination server.**

The CA private key stays on the operator's workstation (encrypted with age in the repo). The lighthouse only needs the CA certificate (public) to validate peers.

**2. Simpler credential model.** Two credential domains instead of three:

| Domain | Credential | Storage |
|--------|-----------|---------|
| Nebula network | CA key + per-peer signed certs | `network.sops.yaml` (age-encrypted) |
| Remote desktop | Per-peer Guacamole passwords/keys | `network.sops.yaml` (age-encrypted) |

ADR-007's setup SSH key becomes unnecessary. No SSH to the hub for peer management at all.

**3. Group-based firewall.** Certificate groups (`server`, `workstation`) map directly to VISION-001 principle 5 (role-appropriate access):

```yaml
firewall:
  inbound:
    - port: 22
      proto: tcp
      groups:
        - server
        - workstation
    - port: 3389
      proto: tcp
      groups:
        - workstation
```

No per-node nftables rules to maintain on the hub.

**4. Direct peer-to-peer when possible.** Unlike WireGuard hub-and-spoke (which routes all traffic through the VPS), Nebula tries direct UDP hole-punching first and falls back to relay only when needed. Two machines on the same LAN or behind hole-punchable NATs connect directly — lower latency for remote desktop without any configuration.

**5. Cross-platform consistency.** Nebula is userspace on all platforms — same binary, same behavior on Linux, macOS, and Windows. WireGuard's kernel module on Linux vs userspace elsewhere creates behavioral differences.

### Architecture

| Component | Role | Runs on |
|-----------|------|---------|
| Nebula lighthouse | Peer discovery + relay fallback | VPS |
| Nebula agent | Encrypted tunnel endpoint | Every fleet node |
| Nebula CA | Certificate signing (offline) | Operator's workstation only |
| CoreDNS | Internal `.wg` DNS resolution | VPS (unchanged) |
| Guacamole | Remote desktop gateway | VPS (unchanged) |
| `porthole` CLI | Provisioning, state management | Operator's workstation |

The lighthouse replaces the WireGuard hub relay. It is lighter — most traffic flows peer-to-peer rather than through the VPS. Guacamole and CoreDNS remain on the VPS, reachable via the Nebula overlay.

### Peer enrollment flow

```
porthole add spoke-name --role workstation
  → generates Nebula keypair
  → signs certificate with CA key (from sops-encrypted repo state)
  → assigns IP from pool
  → writes peer config bundle

porthole enroll spoke-name
  → transfers config bundle to target node (Magic Wormhole or manual copy)
  → node starts nebula service
  → lighthouse discovers peer automatically
  → no hub/lighthouse config change needed
```

### Hub provisioning

Terraform + cloud-init provisions the VPS with:
- Nebula lighthouse (replaces WireGuard)
- CoreDNS (unchanged)
- Guacamole stack (unchanged)
- Caddy reverse proxy (unchanged)

Cloud-init injects the lighthouse's signed certificate and config. The lighthouse is up at first boot. No SSH needed for ongoing management — the lighthouse learns about new peers from their certificates.

SSH is available over the Nebula tunnel for Ansible configuration management (ADR-006 still applies), but is never exposed to the public internet.

## Alternatives Considered

### WireGuard hub-and-spoke + ADR-007 setup key (current plan) — Superseded

Works, but spoke N+1 requires SSH management infrastructure (age-encrypted setup key, temporary public SSH windows, `hub-ssh-open`/`hub-ssh-close` commands). This is a workaround for WireGuard's architectural limitation, not a solution. Since nothing is deployed, the cost of switching is zero.

### Headscale (self-hosted Tailscale control plane) — Not adopted

Solves spoke N+1 via a coordination server, but locks into the Tailscale client ecosystem. Additional infrastructure to run and maintain. 36.2k stars, BSD-3 license.

### Netmaker — Not adopted

WireGuard-based with its own orchestration layer. Requires Docker, custom client agent. 11.5k stars, Apache 2.0. More moving parts than Nebula for the same outcome.

### NetBird — Not adopted

Requires management server + signal server + STUN/TURN. More infrastructure than a single lighthouse. 23.3k stars, BSD-3/AGPL-3.

### Keep WireGuard, accept SSH exposure — Not adopted

The simplest option. Key-only SSH with `AllowUsers` and fail2ban is well-understood. But it leaves unnecessary attack surface open and conflates provisioning and access credentials unless ADR-007's separation is also adopted, adding complexity.

## Consequences

### Positive

- **No public SSH on the hub, ever.** The lighthouse's only public port is Nebula UDP (default 4242). SSH is tunnel-only.
- **Spoke N+1 is trivial.** Offline cert signing, distribute config, start service. No hub interaction.
- **Simpler credential model.** CA key + Guacamole credentials. Two domains, not three.
- **Direct peer-to-peer.** Lower latency when hole-punching succeeds. VPS relay as fallback.
- **Group-based access control.** Role-appropriate firewall rules without per-node configuration.
- **Battle-tested.** 50,000+ hosts at Slack since 2019.
- **Fully open source.** MIT license, no commercial restrictions.
- **Cross-platform.** Linux, macOS, Windows, iOS, Android — all userspace, consistent behavior.

### Accepted trade-offs

- **Not WireGuard.** Nebula uses its own protocol (Noise framework, AES-256-GCM). It's proven but has a smaller ecosystem. WireGuard documentation and community resources are more abundant.
- **Userspace only.** No kernel module on Linux. Performance is measurably lower than WireGuard's kernel path. At ~10 peers with VPS-mediated remote desktop, the bottleneck is the VPS uplink, not tunnel encryption.
- **Existing code needs adaptation.** The `porthole` CLI, Terraform modules, and cloud-init templates assume WireGuard and must be rewritten for Nebula. This is greenfield work (nothing deployed), not migration.
- **Lighthouse is still a VPS.** The VPS doesn't go away — it runs Nebula lighthouse + CoreDNS + Guacamole instead of WireGuard + CoreDNS + Guacamole. Cost is the same.
- **Learning curve.** The operator is familiar with WireGuard. Nebula's certificate model is conceptually different and requires learning.

### Impact on existing ADRs

| ADR | Impact |
|-----|--------|
| **ADR-004** (WireGuard Hub-and-Spoke) | **Superseded** by this ADR |
| **ADR-007** (Age-Encrypted Setup Key) | **Abandoned** — the setup SSH key is unnecessary when spoke N+1 doesn't require SSH |
| **ADR-005** (Remote Desktop / Guacamole) | Unchanged — Guacamole runs on the VPS regardless of tunnel layer |
| **ADR-006** (Terraform + Ansible) | Unchanged — Ansible configures Nebula instead of WireGuard; Terraform still provisions the VPS |

### Impact on existing artifacts

| Artifact | Impact |
|----------|--------|
| VISION-001 | Architecture overview references WireGuard — needs update to Nebula |
| EPIC-001 | References WireGuard relay — needs update |
| EPIC-007 | Hub provisioning — Nebula lighthouse replaces WireGuard hub |
| `porthole` CLI | WireGuard key generation → Nebula cert signing |
| Terraform modules | cloud-init: WireGuard config → Nebula lighthouse config |
| TUI screens | Hub check flow simplified (no SSH setup key management) |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-03-07 | — | Based on SPIKE-009 WireGuard vs Nebula comparison |
| Adopted | 2026-03-07 | — | Decision adopted; ADR-004 superseded |
