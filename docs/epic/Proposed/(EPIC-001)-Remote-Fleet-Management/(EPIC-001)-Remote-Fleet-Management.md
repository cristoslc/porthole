# EPIC-001: Remote Fleet Management

**Status:** Proposed
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Private-Remote-Access-Platform/(VISION-001)-Private-Remote-Access-Platform.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 9b4365e | Initial creation |

---

## Goal

Establish a reliable, private, low-maintenance remote access layer across a
personal fleet of ~10 machines (Linux, macOS, and Windows) — including 6-7
home machines and 2+ remote family machines — so that any managed machine can
be reached via remote desktop
or SSH from any other managed machine, without depending on third-party relay
infrastructure or manual per-machine network configuration.

## Scope boundaries

**In scope:**

- Network connectivity layer (mesh VPN or overlay network) provisioned and
  managed by this repo's Ansible automation (Linux and macOS).
- Remote desktop access (RustDesk) configured to use the chosen network layer.
- SSH access over the chosen network layer.
- Onboarding of remote family machines with minimal friction for non-technical
  family members.
- Network isolation: the remote-access network should be segmented from
  existing infrastructure (VMs, Docker containers) already on the tailnet.
- **Windows machines:** Documented manual setup procedures for the network
  agent and RustDesk. The fleet includes Windows machines (home and family);
  all chosen tools must have native Windows clients.

**Out of scope:**

- Windows provisioning automation (Ansible via WinRM, PowerShell DSC, etc.) —
  Windows machines are configured manually or via a future automation effort.
- General infrastructure management (monitoring, patching, config management)
  of family machines beyond connectivity and remote desktop.
- Mobile device management (phones, tablets).
- File sync or backup for family machines (covered by other PRDs for personal
  machines only).

## Success criteria

1. Any two managed machines can establish a remote desktop session within 30
   seconds, regardless of NAT or firewall topology.
2. SSH access works between all managed machines via stable hostnames or IPs.
3. Remote family machines are reachable without requiring the family member to
   perform any ongoing technical steps after initial setup.
4. The remote-access network is isolated from existing infrastructure —
   RustDesk-only machines cannot reach VMs, Docker containers, or other
   services on the existing tailnet.
5. `make apply` on a managed Linux/macOS workstation configures the network
   layer and RustDesk client automatically. Windows machines have a documented
   manual setup procedure that can be completed in under 15 minutes.
6. No session traffic (signaling or relay) passes through third-party
   infrastructure.

## Child artifacts

| Type | ID | Title | Status | Notes |
|------|----|-------|--------|-------|
| ADR | [ADR-001](../../adr/Adopted/(ADR-001)-RustDesk-for-Remote-Desktop.md) | RustDesk for Remote Desktop | Adopted | Tool selection decision |
| ADR | [ADR-003](../../adr/Proposed/(ADR-003)-Network-Layer-for-Remote-Fleet.md) | Network Layer for Remote Fleet | Proposed | Tailscale ACLs vs ZeroTier vs WireGuard |
| PRD | [PRD-002](../../prd/Implemented/(PRD-002)-Remote-Desktop/(PRD-002)-Remote-Desktop.md) | Remote Desktop Bootstrap | Implemented | RustDesk + GLI KVM + Remmina install |
| PRD | [PRD-004](../../prd/Draft/(PRD-004)-RustDesk-Self-Hosted-Relay/(PRD-004)-RustDesk-Self-Hosted-Relay.md) | RustDesk Self-Hosted Relay | Draft | Blocked pending ADR-003 outcome |
| PRD | — | Fleet Agent Provisioning | — | Not yet created; scope depends on ADR-003 + repo boundary decision. May live in a separate repo. |
| ADR/Spike | — | Repo Boundary: Fleet Agent vs Workstation | — | How does the fleet-agent repo relate to this workstation repo? (Galaxy role, submodule, or standalone) |

## Key dependencies

- **ADR-003 must be decided first.** The network layer decision determines
  whether PRD-004 (self-hosted relay) is needed, what provisioning work is
  required, and how client configuration works.
- PRD-002 is already implemented — it installed RustDesk but deferred relay
  and network configuration. This epic completes that deferred work.

## Key decisions pending

1. **Network layer** (ADR-003): Tailscale ACL segmentation vs. separate
   Tailscale account vs. self-hosted ZeroTier vs. WireGuard hub-and-spoke.
2. **RustDesk relay necessity**: Depends on ADR-003 outcome. If all machines
   are on a mesh VPN, direct IP connections may eliminate the need for a relay
   entirely.
3. **Family machine onboarding model**: How do non-technical family members
   set up and maintain the network agent on their machines?
4. **Repo boundary**: Should the fleet agent (Tailscale + RustDesk install and
   config) live in a separate repo from the workstation bootstrapper? Not every
   machine that needs remote desktop is a personal dev workstation — family
   machines, lightweight non-coding boxes, and home servers need the network
   layer without the full workstation stack. A separate `fleet-agent` repo
   would:
   - Support Linux, macOS, and Windows as first-class targets.
   - Be runnable independently (no workstation repo dependency).
   - Be invokable from the workstation repo as a dependency (Ansible Galaxy
     role, git submodule, or loose prerequisite — TBD).
   - Own the provisioning PRD and Windows setup docs.

   The integration model (how the workstation repo consumes the fleet agent)
   needs its own ADR or spike. Options include: Ansible Galaxy role,
   git submodule, or standalone repo with loose coupling.
