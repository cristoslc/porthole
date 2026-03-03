---
artifact: SPEC-004
title: Guacamole Remote Desktop Gateway
status: Draft
author: cristos
created: 2026-03-03
last-updated: 2026-03-03
parent-epic: EPIC-001
linked-research:
  - SPIKE-004
  - SPIKE-005
linked-adrs:
  - ADR-005
depends-on:
  - SPEC-003
---

# SPEC-004: Guacamole Remote Desktop Gateway

**Status:** Draft
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [(EPIC-001) Remote Fleet Management](../../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Research:** [(SPIKE-004) Remote Desktop Agent Architecture](../../../research/(SPIKE-004)-Remote-Desktop-Agent-Architecture/(SPIKE-004)-Remote-Desktop-Agent-Architecture.md), [(SPIKE-005) Securing Guacamole on Hub](../../../research/(SPIKE-005)-Securing-Guacamole-on-Hub/(SPIKE-005)-Securing-Guacamole-on-Hub.md)
**ADR:** [(ADR-005) Remote Desktop Access Model](../../../adr/Adopted/(ADR-005)-Remote-Desktop-Access-Model.md)
**Depends on:** [SPEC-003](../Draft/(SPEC-003)-WireGuard-Hub-and-Mesh-Network/(SPEC-003)-WireGuard-Hub-and-Mesh-Network.md) (WireGuard network must exist)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-03 | 6297014 | Initial creation |

---

## Problem Statement

The fleet needs browser-based remote desktop access to workstations across
the mesh. ADR-005 adopted Guacamole as the gateway, replacing RustDesk's
agent-based model. Guacamole connects to native remote desktop protocols
already present on target machines (RDP on Windows, xrdp on Linux, Screen
Sharing/VNC on macOS), providing a single browser UI without installing any
client software.

SPIKE-005 established the security model: Guacamole runs on the VPS hub,
bound to the WireGuard interface so it is unreachable from the public
internet. TLS via DNS-01 (Cloudflare). TOTP for authentication with subnet
bypass for connections originating from the WireGuard network.

This spec defines the target state of the Guacamole deployment and the
native protocol enablement on target machines.

## External Behavior

After this spec is implemented:

1. The operator opens `https://guac.yourdomain.wg` in a browser from any
   machine on the WireGuard mesh and sees a Guacamole login page.
2. After authenticating, the operator sees a list of all fleet workstations
   with pre-configured RDP/VNC/SSH connections.
3. Clicking a connection opens a remote desktop session in the browser.
4. Family workstations are accessible via remote desktop without any software
   installation on the operator's machine (browser only).
5. Native remote desktop services on target machines (xrdp, Screen Sharing,
   RDP) are configured and running as background services.

## Acceptance Criteria

1. `docker compose up -d` on the hub starts guacd, Tomcat (Guacamole web
   app), PostgreSQL, and Caddy — all healthy within 60 seconds.
2. Guacamole web UI is accessible at `https://guac.hub.wg` from a peer on
   the WireGuard mesh.
3. Guacamole web UI is **not** accessible from the VPS public IP — all
   services bind to `10.100.0.1` or `127.0.0.1`.
4. TLS certificate is valid (DNS-01 via Cloudflare, no browser warnings).
5. Login with database credentials + TOTP succeeds.
6. Login from a WireGuard subnet IP (`10.100.0.0/24`) bypasses TOTP.
7. Pre-seeded connections for all workstation/family peers (from
   `network.sops.yaml`) are visible after login.
8. RDP connection to a Windows peer succeeds via Guacamole.
9. xrdp connection to a Linux peer succeeds via Guacamole.
10. VNC connection to a macOS peer (Screen Sharing) succeeds via Guacamole.
11. SSH connection to any peer succeeds via Guacamole.

## Scope & Constraints

### In scope

- **Docker Compose stack on hub**:
  - `guacd` — Guacamole connection proxy (protocol handler)
  - `guacamole` — Tomcat web application
  - `postgres` — User/connection database
  - `caddy` — Reverse proxy with TLS (xcaddy build with Cloudflare DNS
    plugin for DNS-01 challenges)
- **Network binding**: All containers bind to `10.100.0.1` (WireGuard
  interface) or `127.0.0.1` (loopback for inter-container communication).
  No ports exposed on public interfaces.
- **TLS via DNS-01**: Caddy obtains certificates using Cloudflare DNS-01
  challenge. No public HTTP/HTTPS ports required. Domain:
  `guac.hub.wg` (internal) with a Cloudflare-managed subdomain for
  certificate issuance.
- **Connection seeding**: SQL script generated from `network.sops.yaml` that
  populates Guacamole's database with connections for each workstation/family
  peer. Protocol selection based on peer role and OS:
  - Linux workstations: xrdp (RDP on port 3389) + SSH
  - macOS workstations: VNC (Screen Sharing on port 5900) + SSH
  - Windows workstations: RDP (port 3389) + SSH (if available)
  - Servers: SSH only
- **Authentication**: Database auth (local users) + TOTP extension. TOTP
  bypass for connections from the WireGuard subnet (`10.100.0.0/24`) —
  being on the mesh is sufficient proof of authorization.
- **Native protocol enablement on targets**:
  - **Linux**: Install and enable `xrdp` (systemd service). Configure to
    use Xorg session backend.
  - **macOS**: Enable Screen Sharing via `kickstart` command. Configure VNC
    password for Guacamole access.
  - **Windows**: Document manual steps to enable RDP (Settings > System >
    Remote Desktop) and confirm WireGuard firewall allows RDP from
    `10.100.0.0/24`.

### Out of scope

- **WireGuard network setup**: Covered by SPEC-003. This spec assumes the
  mesh is operational.
- **Guacamole user management UI/SSO**: MVP uses a single operator account.
  Multi-user or LDAP/SAML integration is a future enhancement.
- **Recording or audit logging**: Not needed for a personal fleet.
- **Guacamole clustering or HA**: Single hub instance is sufficient.
- **Client software installation**: The entire point of Guacamole is
  browser-only access. No client-side software needed.

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| SPEC-003 | Spec | WireGuard mesh must be operational; hub at 10.100.0.1 |
| ADR-005 | Decision | Guacamole gateway + native protocols is the adopted model |
| SPIKE-004 | Research | Guacamole selected over RustDesk/NoMachine for R10 compliance |
| SPIKE-005 | Research | Security model: WireGuard binding, TOTP, DNS-01 TLS |
| Docker + Docker Compose | Runtime | Hub must have Docker installed |
| Cloudflare API token | Secret | For DNS-01 TLS certificate provisioning |

## Design

### Docker Compose architecture

```
                    WireGuard Interface (10.100.0.1)
                              |
                         +----+----+
                         |  Caddy  |  :443 (HTTPS)
                         | xcaddy  |  DNS-01 TLS
                         +----+----+
                              |
                         +----+----+
                         |Guacamole|  :8080 (internal)
                         | Tomcat  |
                         +----+----+
                              |
                    +---------+---------+
                    |                   |
               +----+----+        +----+----+
               |  guacd  |        |PostgreSQL|
               | :4822   |        |  :5432   |
               +---------+        +----------+
```

All containers share a Docker network. Only Caddy binds to the WireGuard
interface. All other services bind to loopback or the Docker bridge only.

### Caddy configuration

```
guac.hub.wg {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy guacamole:8080
}
```

Caddy is built with `xcaddy` including the `caddy-dns/cloudflare` plugin for
DNS-01 challenge support. The Caddyfile binds to `10.100.0.1:443`.

### Connection seeding

A template script generates SQL `INSERT` statements from `network.sops.yaml`:

```sql
-- Generated from network.sops.yaml
INSERT INTO guacamole_connection (connection_name, protocol)
VALUES ('desktop-linux', 'rdp');

INSERT INTO guacamole_connection_parameter (connection_id, parameter_name, parameter_value)
VALUES (currval('guacamole_connection_connection_id_seq'), 'hostname', '10.100.0.2'),
       (currval('guacamole_connection_connection_id_seq'), 'port', '3389');
```

The seeding script runs on first deployment and can be re-run when peers are
added to the state file.

### Native protocol enablement

| Platform | Protocol | Service | Setup |
|----------|----------|---------|-------|
| Linux | RDP | xrdp | `apt install xrdp`, `systemctl enable --now xrdp`, configure Xorg session |
| macOS | VNC | Screen Sharing | `sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -activate -configure -access -on -allowAccessFor -allUsers -privs -all -clientopts -setvnclegacy -vnclegacy yes -setvncpw -vncpw <password>` |
| Windows | RDP | Remote Desktop | Manual: Settings > System > Remote Desktop > On. Windows Firewall: allow RDP from 10.100.0.0/24. Documented in setup guide. |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Guacamole resource usage on minimal VPS | OOM or degraded performance | PostgreSQL tuned for low memory; guacd scales with connections, idle usage is minimal |
| xrdp session conflicts with local display | User sees black screen or login loop | Configure xrdp to use a separate Xorg session; document polkit rules |
| macOS Screen Sharing VNC compatibility | Guacamole can't connect to macOS VNC | SPIKE-004 confirmed VNC works; may need `RFB` protocol tweaks in Guacamole |
| DNS-01 rate limits (Let's Encrypt) | Cannot obtain TLS certificate | Use staging endpoint for testing; production rate limits are generous for single-domain use |
| Docker Compose not available on hub | Cannot deploy stack | EPIC-005 (VPS Bootstrap) ensures Docker is installed; this spec documents the requirement |
