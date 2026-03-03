---
artifact: ADR-005
title: Remote Desktop Access Model
status: Adopted
author: cristos
created: 2026-02-28
last-updated: 2026-02-28
supersedes: ADR-001
linked-epics:
  - EPIC-001
  - EPIC-002
linked-specs:
  - SPEC-002
depends-on: []
---

# ADR-005: Remote Desktop Access Model

**Status:** Adopted
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Epic:** [(EPIC-001) Remote Fleet Management](../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Informed by:** [(SPIKE-004) Remote Desktop Agent Architecture](../../research/(SPIKE-004)-Remote-Desktop-Agent-Architecture/(SPIKE-004)-Remote-Desktop-Agent-Architecture.md)
**Supersedes:** [(ADR-001) RustDesk for Remote Desktop](../Superseded/(ADR-001)-RustDesk-for-Remote-Desktop.md)
**Affects:** EPIC-001, EPIC-002, SPEC-002
**Informed by:** [(SPIKE-005) Securing Guacamole on Hub](../../research/(SPIKE-005)-Securing-Guacamole-on-Hub/(SPIKE-005)-Securing-Guacamole-on-Hub.md), [(SPIKE-006) WireGuard Fallback & Recovery](../../research/(SPIKE-006)-WireGuard-Fallback-Recovery/(SPIKE-006)-WireGuard-Fallback-Recovery.md), [(SPIKE-007) Ephemeral VPS Hub Feasibility](../../research/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Adopted | 2026-02-28 | 6d1cb09 | Created directly as Adopted; informed by SPIKE-004 research |

---

## Context

ADR-001 selected RustDesk as the remote desktop tool. SPEC-002 implemented RustDesk installation on Linux/macOS workstations. Since then, two things changed:

1. **R10 (silent background operation)** was added to the vision. RustDesk has an open bug on macOS where hiding the tray icon breaks keyboard input, and Linux headless mode requires a full GNOME desktop + dummy X11 driver. These platform-specific issues make RustDesk unreliable as a silent background agent across all three platforms.

2. **The network layer changed to WireGuard hub-and-spoke (ADR-004).** All machines are now on a private WireGuard network with stable IPs and DNS names (`.wg`). This means any protocol that works over TCP/IP — including native RDP, VNC, and SSH — works between any two fleet nodes without relay infrastructure.

With a reliable network layer in place, the question shifts from "which remote desktop agent do we install everywhere?" to "do we need a custom agent at all, or can we use native protocols through a centralized gateway?"

SPIKE-004 evaluated three approaches: RustDesk (local agent), NoMachine (local agent), and Apache Guacamole (centralized gateway using native protocols).

## Decision

**Adopt Apache Guacamole as the primary remote desktop gateway, using native OS protocols on target machines. No custom remote desktop agent is installed on targets.**

### How it works

1. A Guacamole server (guacd + web app + database) runs on the VPS hub, accessible only from within the WireGuard network (SPIKE-005).
2. Target machines run only their native remote access services:
   - **Windows:** Built-in RDP (Remote Desktop, port 3389)
   - **Linux:** xrdp for desktop access, sshd for terminal
   - **macOS:** Screen Sharing (VNC, port 5900), Remote Login (SSH)
3. The operator opens a browser, navigates to the Guacamole UI, and connects to any machine by name. Guacamole reaches targets via their WireGuard IPs (`<name>.wg`).
4. SSH and remote desktop are unified in one interface.

### Why not local agents

| Issue | RustDesk | NoMachine |
|-------|----------|-----------|
| macOS silent operation | Broken (hide-tray disables keyboard) | Works, but notification balloons can't be suppressed |
| Linux headless | Requires GNOME + dummy X11 | Works (embedded virtual framebuffer) |
| Maintenance burden | Agent on 10 machines to update | Agent on 10 machines to update |
| SSH coverage | None | Free tier: none |
| Licensing risk | Open source (safe) | Closed source; free tier could change |

NoMachine is the stronger local agent, but it still means maintaining a custom agent on every machine when native protocols — already built into every OS — do the same job. The WireGuard network makes native protocols viable; Guacamole makes them convenient.

### What Guacamole provides

- **Browser-based access** — no client software on the operator's machine
- **Unified SSH + desktop** — one interface for all protocols
- **Zero agents on targets** — native OS services only (R10 satisfied trivially)
- **Session recording** — playback of past sessions if needed
- **TOTP/MFA** — authentication at the gateway
- **Connection management** — all 10 machines defined once, accessible by name

### Limitations accepted

- **macOS desktop quality is lower** than a native ARD client. Guacamole connects via VNC to macOS Screen Sharing, which lacks Apple Remote Desktop protocol optimizations. Acceptable for occasional remote support; not ideal for extended desktop use.
- **Performance overhead.** guacd renders the remote display server-side and re-encodes for browser delivery. Latency is higher than native RDP or NX clients. Acceptable for a personal fleet over WireGuard.
- **Gateway is on-demand, not always-on.** Under the ephemeral hub model (SPIKE-007), Guacamole runs only when the operator needs remote desktop access. The hub is created from scratch, Guacamole starts as part of Docker Compose, and the hub is destroyed afterward. When the hub is down, browser-based access is unavailable — direct SSH and RDP/VNC via native clients remain available as fallback over WireGuard (if the hub is running in hybrid mode) or via the defense-in-depth fallback stack (SPIKE-006).
- **Infrastructure complexity.** Guacamole requires Tomcat + guacd + PostgreSQL. Mitigated by deploying as a Docker Compose stack on the VPS hub, with connections seeded from repo state (SPIKE-005).
- **RustDesk pre-installed as Layer 5 fallback.** RustDesk is installed on all fleet nodes during provisioning as emergency break-glass tooling (SPIKE-006 Layer 5). When WireGuard is down and all other recovery layers have failed, the operator connects via RustDesk's public relay. This is not the primary remote desktop solution — it is dormant infrastructure for emergencies only.

### Fallback

If macOS VNC performance through Guacamole is unacceptable for a specific use case, install NoMachine on that macOS target as a supplement. NoMachine's NX protocol is the highest-performance option for remote desktop. This is a per-machine exception, not a fleet-wide deployment.

### Guacamole security model (SPIKE-005)

- All services bind to the WireGuard interface (`10.100.0.1`) only — Guacamole is unreachable from the public internet.
- Caddy reverse proxy with DNS-01 TLS via Cloudflare (browser-trusted certs, no public exposure).
- Database auth + TOTP, with TOTP bypass for connections from the WireGuard subnet.
- Connections seeded from SQL generated from `network.sops.yaml` — the hub is fully rebuildable from repo state.
- Docker Compose deployment: guacd, guacamole (Tomcat), PostgreSQL, Caddy.

## Consequences

### For ADR-001 (RustDesk)

ADR-001 is **superseded**. RustDesk is no longer the selected remote desktop tool. SPEC-002 (which installed RustDesk) should be revisited — the RustDesk installation can be removed in favor of enabling native RDP/VNC/SSH and deploying the Guacamole gateway.

### For EPIC-001

The "remote desktop agent" component of EPIC-001 simplifies from "install and configure RustDesk on every machine" to "enable native remote desktop protocol on every machine." The provisioning work shifts to:
- Enabling and configuring RDP on Windows (manual, documented steps)
- Installing and configuring xrdp on Linux (automatable via the bootstrap)
- Enabling Screen Sharing on macOS (automatable via `kickstart`)
- Deploying the Guacamole Docker stack on the VPS hub

### For EPIC-002 (Provisioning CLI)

The `wgmesh` CLI or bootstrap may include a step to enable native remote access services on provisioned nodes, rather than installing a third-party agent.

### For the operator dashboard (EPIC-004)

Guacamole partially overlaps with EPIC-004 (Operator Dashboard) — it provides a web UI showing all machines with connection status. The dashboard epic should be scoped to avoid duplicating what Guacamole already provides.

## Alternatives considered

### RustDesk (ADR-001 status quo) — Superseded

Open source, cross-platform, peer-to-peer. But macOS silent operation is broken (open bug), Linux headless requires GNOME + dummy X11, and it doesn't cover SSH. With WireGuard providing the network layer, RustDesk's built-in relay/NAT-traversal adds no value.

### NoMachine Free — Not adopted as primary

Best performance (NX protocol), clean background operation on all platforms, embedded virtual framebuffer on Linux. Not adopted as primary because: (a) closed source with changeable license terms, (b) still requires a per-machine agent when native protocols suffice, (c) free tier has no SSH support. Retained as a fallback for macOS targets where Guacamole's VNC performance is insufficient.

### Hybrid: Guacamole + RustDesk/NoMachine everywhere — Rejected

Installing both a gateway and per-machine agents adds complexity without proportional benefit. The gateway alone covers the common case; agents are only justified as per-machine exceptions.

