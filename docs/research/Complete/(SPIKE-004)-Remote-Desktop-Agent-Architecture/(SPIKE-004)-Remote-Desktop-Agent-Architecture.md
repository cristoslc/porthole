---
artifact: SPIKE-004
title: Remote Desktop Agent Architecture
status: Complete
author: cristos
created: 2026-02-28
last-updated: 2026-02-28
parent-epic: EPIC-001
depends-on: []
question: "Can RustDesk and NoMachine run as silent background agents while also acting as clients, or should the fleet use a gateway model like Apache Guacamole instead?"
gate: "Determine which model (local agent or gateway) satisfies R10 (silent background operation), R3 (cross-platform), R6 (family passive after setup), and R8 (low maintenance) across Linux, macOS, and Windows"
---

# SPIKE-004: Remote Desktop Agent Architecture

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent:** [EPIC-001](../../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Question:** Can RustDesk and NoMachine run as silent background agents while also acting as clients, or should the fleet use a gateway model like Apache Guacamole instead?
**Gate:** Pre-MVP
**Risks addressed:**
  - R10 (silent background operation) may not be achievable with peer-to-peer desktop agents
  - Agent-per-machine model may impose maintenance burden incompatible with R8 (low maintenance)
**Blocks:** ADR-005 (Remote Desktop Access Model)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-28 | 6d1cb09 | Research completed in conversation; findings inform ADR-005 |

---

## Question

The fleet requires remote desktop access across Linux, macOS, and Windows (R3). Requirement R10 mandates that all agents run silently in the background with no foreground windows or user interaction. Two architectural models exist:

1. **Local agent model:** Install a desktop agent (RustDesk, NoMachine) on every machine. Each agent accepts incoming connections and can initiate outgoing ones.
2. **Gateway model:** Run a centralized gateway (Apache Guacamole) that connects to target machines using their native protocols (RDP, VNC, SSH). No custom agent on targets.

Which model satisfies R10, R3, R6 (family passive after setup), and R8 (low maintenance)?

## Go / No-Go Criteria

- **Go (local agent):** The chosen agent runs as a background service on all three platforms with no foreground window, supports simultaneous server+client operation, and can be deployed/configured via automation.
- **Go (gateway):** Guacamole provides acceptable desktop performance over WireGuard for all three platforms, and native protocol setup on targets is automatable.
- **No-go:** If neither model satisfies R10 across all platforms, a hybrid or alternative approach is needed.

## Pivot Recommendation

If local agents fail R10 on macOS (most likely failure point), adopt a hybrid: Guacamole gateway for centralized access + native Screen Sharing/RDP/xrdp on targets, with a local agent only on platforms where it works cleanly.

## Findings

### RustDesk background operation

RustDesk runs as a background service on all three platforms. Server and client processes coexist — the service (`--server`) handles incoming connections while the GUI can independently initiate outgoing ones.

**Platform assessment:**

| Platform | Service model | Silent operation | Key issues |
|----------|--------------|-----------------|------------|
| Linux | systemd unit (`rustdesk.service`) | Yes | Requires active display session (lightdm + GNOME + xserver-xorg-video-dummy for headless). Wayland headless not supported. |
| macOS | LaunchDaemon + LaunchAgent | Partial | `hide-tray=Y` breaks keyboard input (open issue). Screen Recording / Accessibility permissions require GUI or MDM grant. FileVault blocks pre-login. |
| Windows | Windows Service (SCM) | Yes | Quitting the tray icon uninstalls the service. UAC desktop-switching has edge cases. |

**R10 verdict:** Linux and Windows satisfy R10. macOS has an open bug where hiding the tray icon breaks keyboard input — R10 is not fully met on macOS.

### NoMachine background operation

NoMachine installs as a system service by default on all platforms. Server and client components coexist with no conflict. On Linux, it can spin up its own virtual framebuffer when no physical display exists — no dummy X11 driver needed.

**Platform assessment:**

| Platform | Service model | Silent operation | Key issues |
|----------|--------------|-----------------|------------|
| Linux | `nxserver.service` (systemd) | Yes | Embedded virtual framebuffer for headless. GNOME not required. |
| macOS | LaunchDaemon + LaunchAgent | Yes (icon hideable) | Balloon notifications cannot be fully suppressed (v8+ security feature). Permissions still need GUI/MDM grant. |
| Windows | Windows Services (multiple) | Yes | Clean service architecture. |

**R10 verdict:** All three platforms satisfy R10. Tray icon hideable via `DisplayMonitorIcon 0`. Notification balloons are a minor cosmetic issue, not a functional one.

**Licensing:** Free edition allows 1 concurrent incoming connection, which is sufficient for a personal fleet (operator connects to one machine at a time). No virtual desktops, no browser access, no SSH tunneling in free tier. Enterprise Desktop ~$44.50/machine/year.

### Apache Guacamole (gateway model)

Guacamole is a centralized gateway, not a peer-to-peer agent. One server runs guacd + Tomcat + database. It connects to targets using their native protocols. Users access everything through a browser.

**Architecture:**
```
Browser → HTTPS → Tomcat (web app) → TCP 4822 → guacd → RDP/VNC/SSH → target
```

**No agent on targets.** Targets only need their native remote protocol enabled:

| Platform | Protocol | What to enable |
|----------|----------|---------------|
| Windows | RDP | Built-in Remote Desktop |
| Linux | RDP / VNC / SSH | xrdp, TigerVNC, or sshd |
| macOS | VNC / SSH | Screen Sharing + Remote Login |

**WireGuard compatibility:** Works transparently. guacd connects to WireGuard IPs. Well-documented homelab pattern.

**Strengths:**
- Zero client software — browser-only access from any device
- Covers SSH + desktop in one gateway (RustDesk/NoMachine are desktop-only)
- No per-machine agent to install, update, or troubleshoot
- Session recording, TOTP/MFA, user management built in
- Open source (Apache 2.0), no per-machine licensing

**Weaknesses:**
- More infrastructure: Tomcat + guacd + PostgreSQL (though Docker Compose simplifies this)
- Performance overhead: server-side rendering + re-encoding for browser delivery. Native RDP/NX clients outperform it for latency-sensitive work
- macOS via VNC is lower quality than native ARD — no Apple Remote Desktop protocol optimizations
- No USB device redirection
- Single point of failure (the gateway server)

**R10 verdict:** Not applicable — there is no agent on targets. Native RDP/VNC/SSH services run as OS-level background services by default. R10 is inherently satisfied.

### Comparison matrix

| Criterion | RustDesk | NoMachine Free | Guacamole |
|-----------|----------|---------------|-----------|
| R3: Cross-platform desktop | Yes | Yes | Yes (VNC/RDP) |
| R6: Family passive after setup | Yes (agent auto-starts) | Yes (service auto-starts) | Yes (native services auto-start) |
| R8: Low maintenance | Agent updates on 10 machines | Agent updates on 10 machines | 1 gateway to maintain, 0 agents |
| R10: Silent background | Partial (macOS broken) | Yes | Yes (no agent) |
| SSH coverage | No | No (free) | Yes |
| Client required | RustDesk app | NoMachine Player | Browser only |
| Operator UX | Native app, fast | Native app, fastest (NX protocol) | Browser, adequate |
| macOS target quality | Good (when working) | Good | Mediocre (VNC only) |
| Cost (10 machines) | Free | Free (1 connection) | Free |
| Infrastructure | Peer-to-peer via WireGuard | Peer-to-peer via WireGuard | Gateway server (Docker) |

### Key insight: hybrid model

No single tool is best at everything. The natural split:

- **Guacamole** for centralized, browser-based access to all machines (SSH + desktop). Runs on the operator's homelab or the VPS. Zero agents on targets. Satisfies R10 trivially.
- **Native protocols only on targets**: RDP on Windows, xrdp on Linux, Screen Sharing on macOS, sshd everywhere. These are OS services that run silently by default.
- **RustDesk or NoMachine** only if Guacamole's VNC-to-macOS performance is unacceptable, and only on macOS targets where it matters.

This eliminates the per-machine agent maintenance burden entirely for the common case.
