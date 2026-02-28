# EPIC-001: Remote Fleet Management

**Status:** Proposed
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

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
- Remote desktop access via Guacamole gateway using native protocols (RDP, VNC, SSH).
- SSH access over the chosen network layer.
- Onboarding of remote family machines with minimal friction for non-technical
  family members.
- Network isolation: the remote-access network should be segmented from
  existing infrastructure (VMs, Docker containers) already on the tailnet.
- **Windows machines:** Documented manual setup procedures for the network
  agent and RDP enablement. The fleet includes Windows machines (home and
  family); all chosen tools must have native Windows clients.

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
| Spike | [SPIKE-001](../../research/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions.md) | Remote Desktop and Mesh Networking Solutions | Complete | Evaluation of 11 OSS remote desktop + 7 mesh networking solutions |
| Spike | [SPIKE-002](../../research/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation.md) | Commercial Remote Desktop Solution Evaluation | Complete | Comparative analysis of 11 commercial remote desktop tools |
| Spike | [SPIKE-004](../../research/(SPIKE-004)-Remote-Desktop-Agent-Architecture/(SPIKE-004)-Remote-Desktop-Agent-Architecture.md) | Remote Desktop Agent Architecture | Complete | RustDesk vs NoMachine vs Guacamole for R10 compliance |
| ADR | [ADR-001](../../adr/Superseded/(ADR-001)-RustDesk-for-Remote-Desktop.md) | RustDesk for Remote Desktop | Superseded | Superseded by ADR-005 (Guacamole gateway model) |
| ADR | [ADR-003](../../adr/Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md) | Network Layer for Remote Fleet | Abandoned | Evaluated Tailscale vs ZeroTier vs WireGuard; superseded by ADR-004 |
| ADR | [ADR-004](../../adr/Adopted/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) | WireGuard Hub-and-Spoke Relay | Adopted | Self-hosted WireGuard via VPS; replaces ADR-003 |
| ADR | [ADR-005](../../adr/Adopted/(ADR-005)-Remote-Desktop-Access-Model.md) | Remote Desktop Access Model | Adopted | Guacamole gateway + native protocols; replaces ADR-001 |
| Spec | [SPEC-002](../../spec/Deprecated/(SPEC-002)-Remote-Desktop/(SPEC-002)-Remote-Desktop.md) | Remote Desktop Bootstrap | Deprecated | ADR-005 supersedes RustDesk with Guacamole + native protocols |
| PRD | [PRD-004](../../prd/Abandoned/(PRD-004)-RustDesk-Self-Hosted-Relay/(PRD-004)-RustDesk-Self-Hosted-Relay.md) | RustDesk Self-Hosted Relay | Abandoned | WireGuard mesh eliminates the need for a relay |

## Key dependencies

- **ADR-004 (Adopted):** WireGuard hub-and-spoke via VPS is the chosen network
  layer. ADR-003 (Tailscale ACLs recommendation) was abandoned in favor of
  self-hosted WireGuard for vendor independence and operational sovereignty.
- **ADR-005 (Adopted):** Guacamole gateway + native protocols replaces RustDesk
  as the remote desktop model. SPEC-002 (RustDesk install) needs to be
  revisited to reflect this change.
- PRD-004 (RustDesk relay) is Abandoned — the WireGuard mesh eliminates the
  need for a self-hosted relay.

## Key decisions pending

1. **Family machine onboarding model**: How do non-technical family members
   set up and maintain the WireGuard client on their machines?
2. **Repo boundary**: Should the fleet agent (WireGuard + native protocol
   enablement) live in a separate repo from the workstation bootstrapper? Not
   every machine that needs remote access is a personal dev workstation —
   family machines, lightweight non-coding boxes, and home servers need the
   network layer without the full workstation stack.
3. **Guacamole deployment**: Where does the Guacamole gateway run — on the
   operator's homelab, on the VPS, or both? How does it integrate with the
   WireGuard network?
