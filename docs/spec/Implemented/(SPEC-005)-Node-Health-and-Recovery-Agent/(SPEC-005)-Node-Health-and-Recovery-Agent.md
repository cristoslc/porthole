---
artifact: SPEC-005
title: Node Health & Recovery Agent
status: Implemented
author: cristos
created: 2026-03-03
last-updated: 2026-03-03
parent-epic: EPIC-001
linked-research:
  - SPIKE-006
linked-adrs: []
depends-on:
  - SPEC-003
---

# SPEC-005: Node Health & Recovery Agent

**Status:** Implemented
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [(EPIC-001) Remote Fleet Management](../../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Research:** [(SPIKE-006) WireGuard Fallback & Recovery](../../../research/(SPIKE-006)-WireGuard-Fallback-Recovery/(SPIKE-006)-WireGuard-Fallback-Recovery.md)
**Depends on:** [SPEC-003](../Implemented/(SPEC-003)-WireGuard-Hub-and-Mesh-Network/(SPEC-003)-WireGuard-Hub-and-Mesh-Network.md) (WireGuard network must exist)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-03 | 6297014 | Initial creation; MVP scope is Layers 1-2 from SPIKE-006 |
| Implemented | 2026-03-03 | 068a4f5 | wg-watchdog, reverse SSH tunnel, gen-peer-scripts command |

---

## Problem Statement

WireGuard tunnels are stateless and silent — when connectivity breaks (ISP
outage, NAT rebinding, hub IP change, post-sleep interface failure), there is
no built-in mechanism to detect the problem or recover. The operator has no
way to reach a remote machine if the WireGuard tunnel is down, and family
members cannot be expected to diagnose or fix network issues.

SPIKE-006 designed a five-layer recovery model. This spec covers the MVP
(Layers 1 and 2) plus a post-MVP placeholder for Layer 5:

- **Layer 1 (Watchdog):** Detect tunnel failure and auto-recover.
- **Layer 2 (Reverse SSH):** Out-of-band access when WireGuard is completely
  down.
- **Layer 5 (Post-MVP):** RustDesk as a dormant last-resort fallback.

## External Behavior

After this spec is implemented:

1. If a peer's WireGuard tunnel goes down (hub unreachable), the watchdog
   detects the failure within 2 minutes and attempts automatic recovery
   (interface restart, DNS re-resolution).
2. If the tunnel cannot be restored, the operator can still reach the machine
   via reverse SSH tunnel through the VPS public IP.
3. After a laptop wakes from sleep, the WireGuard tunnel reconnects
   automatically without user intervention.
4. The operator can `ssh -p 220N vps-public-ip` to reach any node's reverse
   SSH tunnel, regardless of WireGuard status.

## Acceptance Criteria

### Layer 1: Watchdog

1. On Linux: a systemd timer fires every 2 minutes, pings `10.100.0.1` (hub),
   and restarts the `wg-quick@wg0` service if ping fails 3 consecutive times.
2. On macOS: a launchd plist fires every 2 minutes with the same logic,
   restarting the WireGuard tunnel via `wg-quick`.
3. On Windows: a Task Scheduler task fires every 2 minutes with the same
   logic, restarting the WireGuard tunnel service.
4. The watchdog runs `reresolve-dns.sh` on every invocation to handle hub IP
   changes.
5. After a sleep/resume event (Linux: systemd-sleep hook; macOS: launchd
   wake notification; Windows: Task Scheduler wake trigger), the watchdog
   fires immediately rather than waiting for the next timer interval.
6. Watchdog logs to syslog/journald (Linux), system log (macOS), or Event
   Log (Windows) with sufficient detail for debugging.

### Layer 2: Reverse SSH Tunnel

7. Each peer maintains a persistent outbound SSH connection to the VPS
   public IP (not through WireGuard) with a remote port forward:
   `-R 0.0.0.0:220N:localhost:22` where N is the peer's index.
8. The reverse SSH tunnel runs as a system service (systemd on Linux, launchd
   on macOS, Windows Service) with `Restart=always` / equivalent.
9. A dedicated `tunnel` user on the VPS has a restricted shell
   (`/bin/false` or `rbash`) — it can only hold port forwards, not execute
   commands.
10. The operator can connect via `ssh -p 220N <vps-public-ip>` to reach any
    peer's SSH daemon, verifiable when WireGuard is intentionally stopped.
11. Hub nftables rules allow inbound SSH on ports 2200-2220 from any source
    (these are the reverse tunnel listening ports).
12. Reverse SSH tunnel reconnects automatically after VPS reboot, network
    interruption, or SSH timeout (using `ServerAliveInterval` +
    `ServerAliveCountMax` + service restart).

## Scope & Constraints

### In scope

#### Layer 1: Watchdog

- **Linux**: systemd timer + service unit. Timer fires every 2 min. Service
  runs a health-check script that pings the hub, runs `reresolve-dns.sh`,
  and restarts WireGuard if needed. systemd-sleep hook for immediate
  post-resume check.
- **macOS**: launchd plist with `StartInterval=120`. Same health-check
  script adapted for macOS (`wg-quick` path, `scutil` for DNS, wake
  notification via `com.apple.wake` or `SleepWatcher`).
- **Windows**: Task Scheduler task with 2-minute repeat trigger. PowerShell
  health-check script. Wake trigger for post-sleep recovery.
- **`reresolve-dns.sh`**: Resolves `hub.yourdomain.com`, compares to current
  WireGuard endpoint, updates via `wg set` if changed.

#### Layer 2: Reverse SSH Tunnel

- **Deterministic port assignment**: Port `2200 + N` where N is the peer's
  position in `network.sops.yaml`. Example: peer at `10.100.0.5` gets port
  `2205`.
- **SSH config on peers**: `~/.ssh/config` or system-level config with
  `ServerAliveInterval=30`, `ServerAliveCountMax=3`,
  `ExitOnForwardFailure=yes`.
- **Service wrapper**:
  - Linux: systemd service with `Restart=always`, `RestartSec=10`
  - macOS: launchd plist with `KeepAlive=true`
  - Windows: NSSM or native Windows Service wrapping `ssh.exe`
- **VPS `tunnel` user**: Dedicated user, no shell access, SSH key auth only.
  `authorized_keys` restricts each peer's key to port forwarding only via
  `command="/bin/false",no-pty,no-X11-forwarding` prefix.
- **Hub nftables update**: Allow TCP 2200-2220 inbound (reverse tunnel
  listening ports).

#### Layer 5: Post-MVP (placeholder)

- **RustDesk**: Pre-installed on all nodes as a dormant background service.
  Public relay (community or self-hosted). Used only when both WireGuard and
  reverse SSH are unavailable. Not configured or deployed by this spec — only
  documented as the intended Layer 5 approach.

### Out of scope

- **Layer 3 (SMS/Signal alerting)**: Operator notification when watchdog
  cannot recover. Future enhancement.
- **Layer 4 (OS-level remote access)**: Intel AMT, IPMI, iDRAC for hardware-
  level recovery. Not applicable to consumer hardware.
- **Monitoring dashboard**: Health data visualization is EPIC-004 (Operator
  Dashboard).
- **Automation of deployment**: Ansible roles to deploy watchdog and tunnel
  services are part of the provisioning workflow, not this spec. This spec
  defines the target state and service configurations.

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| SPEC-003 | Spec | WireGuard mesh must exist; hub IP and peer list from state file |
| SPIKE-006 | Research | Five-layer recovery model; this spec implements Layers 1-2 |
| VPS public IP | Infrastructure | Reverse SSH tunnels connect to VPS outside WireGuard |
| SSH server on all peers | Prerequisite | OpenSSH on Linux/macOS; OpenSSH or built-in SSH on Windows |

## Design

### Layer 1: Watchdog flow

```
Every 2 minutes (or on wake):
  1. Run reresolve-dns.sh
     - Resolve hub.yourdomain.com
     - Compare to current WireGuard endpoint
     - If changed: wg set wg0 peer <hub-pubkey> endpoint <new-ip>:51820
  2. Ping 10.100.0.1 (hub WireGuard IP)
  3. If ping fails:
     - Increment failure counter
     - If counter >= 3:
       a. Log "WireGuard tunnel down, restarting"
       b. Restart WireGuard interface (wg-quick down/up)
       c. Reset failure counter
     - Else: log "Ping failed (N/3)"
  4. If ping succeeds:
     - Reset failure counter
```

### Layer 2: Reverse SSH tunnel

```
Persistent service:
  ssh -N -T \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -R 0.0.0.0:220N:localhost:22 \
    tunnel@<vps-public-ip>
```

The service wrapper restarts on exit. The `tunnel` user's
`authorized_keys` restricts each peer key:

```
command="/bin/false",no-pty,no-agent-forwarding,no-X11-forwarding,permitopen="none" ssh-ed25519 AAAA... peer-desktop-linux
```

### Port allocation

| Peer | WireGuard IP | Reverse SSH Port |
|------|-------------|-----------------|
| hub | 10.100.0.1 | N/A (hub itself) |
| desktop-linux | 10.100.0.2 | 2202 |
| desktop-mac | 10.100.0.3 | 2203 |
| mom-imac | 10.100.0.10 | 2210 |

Port = `2200 + last octet of WireGuard IP`.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Watchdog restarts WireGuard during active session | Operator's remote desktop session interrupted | 3-strike threshold reduces false positives; restart is brief (~2s) |
| Reverse SSH tunnel port conflicts on VPS | Two peers assigned same port | Deterministic allocation from state file; `porthole` (EPIC-002) validates uniqueness |
| SSH key management for tunnel user | Key sprawl, stale keys | Keys generated during peer enrollment; tracked in `network.sops.yaml` |
| macOS sleep/wake detection unreliable | Tunnel stays down after laptop wake | Multiple detection methods: SleepWatcher, launchd wake events, fallback to timer-based detection |
| Windows Task Scheduler permissions | Health script can't restart WireGuard tunnel | Task runs as SYSTEM; documented in Windows setup guide |
| Reverse SSH tunnel blocked by corporate firewall | Family member's network blocks outbound SSH | Use port 443 as fallback for reverse SSH; document alternative ports |
