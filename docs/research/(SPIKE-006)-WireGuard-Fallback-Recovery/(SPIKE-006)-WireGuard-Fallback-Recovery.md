# SPIKE-006: WireGuard Fallback & Recovery

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent:** EPIC-008 (Node Agent, proposed)
**Question:** When WireGuard goes down on a remote node, how does the operator regain access to reinstall or reconfigure it?
**Gate:** Pre-MVP
**Risks addressed:**
  - WireGuard failure creates total access blackout (SSH, Guacamole, everything routes through the tunnel)
  - Family members at remote locations cannot troubleshoot networking issues
  - Auto-recovery cannot handle all failure modes — some require human intervention via an out-of-band channel

---

## Question

In a hub-and-spoke WireGuard topology, if WireGuard goes down on a remote node, the operator loses ALL remote access to it. Every management channel (SSH, Guacamole, the TUI) routes through the WireGuard tunnel. What fallback mechanisms allow the operator to reach the node and fix WireGuard?

## Go / No-Go Criteria

- **Go:** At least two independent fallback layers exist, covering both automated recovery and operator-assisted remote access, across all three platforms (Linux, macOS, Windows).
- **No-go:** If no reliable out-of-band channel can be maintained alongside WireGuard without routing conflicts.

## Pivot Recommendation

If an always-on fallback channel proves unreliable alongside WireGuard, fall back to Tailscale as the primary network layer (reverting ADR-004) and accept the SaaS dependency.

## Findings

### Recommended defense-in-depth stack

Five layers, in order of implementation priority:

| Layer | Mechanism | Handles | Human needed? |
|-------|-----------|---------|---------------|
| 1 | Watchdog + auto-restart | Process crashes, stale handshakes, post-sleep recovery | No |
| 2 | Reverse SSH tunnel | WireGuard config errors, hub IP changes, persistent failures | Yes (operator) |
| 3 | Tailscale (pre-installed, passive) | Complete WireGuard stack failure | Yes (operator) |
| 4 | One-click recovery script | Failures requiring local action | Yes (family member on phone) |
| 5 | Side-channel remote desktop | Everything else | Yes (operator via family member) |

### Layer 1: Watchdog + auto-restart

Handles ~80% of real-world failures without human intervention. Most WireGuard "outages" are process crashes, kernel module issues after OS updates, or stale handshakes after sleep/resume.

**Health check:** Ping the hub's WireGuard IP (`10.100.0.1`). If unreachable, restart WireGuard. If still unreachable after restart, escalate (start reverse SSH tunnel, log the failure).

**Linux (systemd timer, runs every 2 minutes):**

```bash
#!/bin/bash
# /usr/local/bin/wg-watchdog.sh
HUB_WG_IP="10.100.0.1"
if ! ping -c 2 -W 5 "$HUB_WG_IP" &>/dev/null; then
    wg-quick down wg0 2>/dev/null || true
    sleep 2
    wg-quick up wg0
    sleep 5
    if ! ping -c 2 -W 5 "$HUB_WG_IP" &>/dev/null; then
        echo "$(date): Recovery FAILED" >> /var/log/wg-watchdog.log
        # Start reverse SSH tunnel as escalation
    fi
fi
```

Plus a systemd override for wg-quick: `Restart=always`, `RestartSec=5`.

Plus a sleep/resume hook: systemd service triggered by `suspend.target` that restarts WireGuard after wake.

**macOS:** launchd plist with `StartInterval` for watchdog. `sleepwatcher` or launchd trigger for post-sleep recovery. The WireGuard.app Network Extension handles most auto-recovery itself, but wg-quick (Homebrew) needs explicit management.

**Windows:** WireGuard Windows Service has built-in service recovery (`sc failure WireGuardTunnel$wg0 reset=0 actions=restart/5000`). Add a PowerShell watchdog via Task Scheduler for ping-based health checks (WindowsWireguardWatchdog pattern).

### Layer 2: Reverse SSH tunnel

An always-on outbound TCP connection from the node to the VPS's public IP (not through WireGuard). Completely independent of WireGuard's health.

**How it works:**
1. The node maintains a persistent SSH connection to `VPS_PUBLIC_IP:22`
2. This connection binds a port on the VPS (e.g., `localhost:2222`) that tunnels back to the node's port 22
3. The operator SSHes to the VPS, then `ssh -p 2222 localhost` to reach the node

**Implementation:** autossh or plain OpenSSH with `ServerAliveInterval` + systemd `Restart=always`. Modern OpenSSH 8.x+ with systemd is sufficient without autossh.

```ini
[Unit]
Description=Reverse SSH fallback tunnel
After=network-online.target

[Service]
User=tunnel
ExecStart=/usr/bin/ssh -N \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes \
  -R 2222:localhost:22 \
  -i /home/tunnel/.ssh/fallback_key \
  tunnel-user@VPS_PUBLIC_IP
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**VPS-side:** `GatewayPorts no` in sshd_config keeps the tunnel port local-only. Each node gets a unique port (node 1 = 2201, node 2 = 2202, etc.).

**Alternatives:** bore (Rust, simpler than autossh), rathole (lower memory), chisel (HTTP-based). All are reverse tunnel tools that don't require sshd on the VPS.

**Port assignment from network state:** The reverse SSH port for each node should be deterministic from the node's peer number in `network.sops.yaml` (e.g., peer N gets port 2200+N). This way the mapping is reproducible from repo state.

### Layer 3: Tailscale (pre-installed, passive)

Tailscale already exists on some machines. It can coexist with WireGuard if configured correctly.

**Coexistence requirements:**
- WireGuard must use split-tunnel (`AllowedIPs = 10.100.0.0/24` only, not `0.0.0.0/0`) so it doesn't capture Tailscale's DERP relay traffic
- On Linux: set `Table = off` in wg0.conf and manage routes manually, or use fwmark-based policy routing to avoid clobbering Tailscale's routing rules
- macOS and Windows are less conflict-prone (Network Extensions / WireGuard NT coexist more gracefully)

**Usage model:** Tailscale sits idle. When WireGuard and the reverse SSH tunnel are both down (rare), the operator connects via Tailscale as a last-resort out-of-band channel.

### Layer 4: One-click recovery script

When all automated and remote channels fail, a family member physically at the machine is the only option. Design for it: a desktop shortcut labeled clearly ("FIX VPN") that restarts WireGuard.

**Linux:** `.desktop` file on Desktop running a bash script with `pkexec` for privilege escalation.

**macOS:** Automator app on Desktop running `wg-quick down wg0 && wg-quick up wg0`.

**Windows:** `.bat` file on Desktop:
```batch
@echo off
net stop WireGuardTunnel$wg0 2>nul
timeout /t 3
net start WireGuardTunnel$wg0
ping 10.100.0.1 -n 3
pause
```

The TUI could also expose a "Restart VPN" action for this scenario.

### Layer 5: Side-channel remote desktop

As a last resort when all automated and remote-operator channels have failed, a commercial remote desktop tool provides out-of-band access that is completely independent of the WireGuard tunnel. The key requirement: a family member at the machine must be able to participate (read a code, click "allow"), so the tool must have a simple, walkthrough-friendly flow.

**Evaluated tools (2026-02-28):**

| Tool | Free tier | Cross-platform | Family-friendly flow | Verdict |
|------|-----------|----------------|---------------------|---------|
| **RustDesk (self-hosted)** | Unlimited (self-hosted relay) | Linux, macOS, Windows | "Read me the 9-digit code" — simple | **Recommended** |
| **Chrome Remote Desktop** | Unlimited | Windows, macOS, Debian-based Linux only | Google account required; "enter this code" flow | Good supplement for Debian/Ubuntu nodes |
| **Quick Assist** | Unlimited | Windows only | Built into Windows; "enter this 6-digit code" | Excellent for Windows nodes |
| **AnyDesk** | Free tier exists | All platforms | Simple code flow | **Disqualified** — flags personal use as commercial with >3 devices |
| **TeamViewer** | Free tier exists | All platforms | Simple code flow | **Disqualified** — aggressive commercial-use detection; sessions limited to 5 min |

**Recommended approach — RustDesk self-hosted:**
- Run `hbbs` (rendezvous) and `hbbr` (relay) on the VPS alongside the other hub services. The relay uses the VPS's public IP directly (TCP/UDP 21115-21119), not the WireGuard tunnel, so it survives WireGuard failures.
- Pre-install the RustDesk client on all fleet nodes. Configure it to point at the self-hosted relay (`relay=<VPS_PUBLIC_IP>`).
- The family member's role: open RustDesk, read the 9-digit ID displayed on screen, and click "Allow" when prompted. The operator connects from any device with RustDesk installed.
- No account creation, no SaaS dependency, no commercial-use detection. The relay and rendezvous server are fully self-hosted.
- Ironic that RustDesk returns as a fallback recovery tool rather than the primary remote desktop solution (see SPIKE-004).

**Supplements:**
- **Chrome Remote Desktop** for Debian/Ubuntu nodes where a Google account is already active. The "generate a one-time code" flow is family-friendly.
- **Quick Assist** (built into Windows 10/11) for Windows nodes. Zero-install, 6-digit code flow, works immediately.

**Family walkthrough:** Pre-write a one-page PDF/printout for each platform: "If Cristos asks you to help fix the VPN, open the app with this icon, read the code." Laminate it. Tape it to the desk. This is the last line of defense.

### Failure mode coverage

| Failure | Layer 1 | Layer 2 | Layer 3 | Layer 4 | Layer 5 |
|---------|---------|---------|---------|---------|---------|
| WireGuard process crash | Yes | — | — | — | — |
| Stale handshake after sleep | Yes | — | — | — | — |
| Corrupt WireGuard config | — | Yes | Yes | Yes | Yes |
| Hub VPS down | — | — | Yes | — | — |
| Node internet down | — | — | — | — | — |
| Kernel/OS update broke WG | — | Yes | Yes | Yes | Yes |
| ISP blocking UDP | — | Yes (TCP) | Yes (DERP/TCP) | — | Yes |
| All remote channels down | — | — | — | Yes | — |

No fallback handles "node internet down" — that requires physical access regardless.

### MVP recommendation

**Layers 1 + 2 are MVP.** The watchdog handles transient failures automatically. The reverse SSH tunnel gives the operator a direct path to fix anything the watchdog cannot. These two cover the vast majority of real-world scenarios.

Layers 3-5 are post-MVP hardening: Tailscale coexistence, desktop recovery scripts, and side-channel remote desktop can be added incrementally.

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-28 | a785ec8 | Research completed in conversation; informs EPIC-008 node agent fallback design |
