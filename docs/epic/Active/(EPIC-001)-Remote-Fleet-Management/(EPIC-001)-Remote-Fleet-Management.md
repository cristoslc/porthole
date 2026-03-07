---
artifact: EPIC-001
title: Remote Fleet Management
status: Active
author: cristos
created: 2026-02-28
last-updated: 2026-03-07
parent-vision: VISION-001
depends-on: []
success-criteria:
  - Any two managed machines establish a remote desktop session within 30 seconds regardless of NAT/firewall
  - SSH access works between all managed machines via stable hostnames or IPs
  - Remote family machines reachable without ongoing technical steps after initial setup
  - Remote-access network isolated from existing infrastructure (VMs, Docker, local services)
  - make apply on Linux/macOS configures Nebula and remote desktop automatically; Windows manual setup under 15 minutes
---

# EPIC-001: Remote Fleet Management

**Status:** Active
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-03-03
**Parent Vision:** [VISION-001](../../../vision/Active/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 616849b | Initial creation |
| Active | 2026-03-03 | 72c4790 | Research complete (7 spikes, 2 ADRs adopted); agent specs created |

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
  existing infrastructure (VMs, Docker containers) already on the node's local network.
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
   remote machines cannot directly reach VMs, Docker containers, or other
   services on the existing local net.
5. `make apply` on a managed Linux/macOS workstation configures the Nebula
   network layer and native remote desktop protocols (xrdp on Linux, Screen
   Sharing on macOS) automatically. Windows machines have a documented manual
   RDP + Nebula setup procedure that can be completed in under 15 minutes.

## Child artifacts

| Type | ID | Title | Status | Notes |
|------|----|-------|--------|-------|
| Spike | [SPIKE-001](../../../research/Complete/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions.md) | Remote Desktop and Mesh Networking Solutions | Complete | Evaluation of 11 OSS remote desktop + 7 mesh networking solutions |
| Spike | [SPIKE-002](../../../research/Complete/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation.md) | Commercial Remote Desktop Solution Evaluation | Complete | Comparative analysis of 11 commercial remote desktop tools |
| Spike | [SPIKE-004](../../../research/Complete/(SPIKE-004)-Remote-Desktop-Agent-Architecture/(SPIKE-004)-Remote-Desktop-Agent-Architecture.md) | Remote Desktop Agent Architecture | Complete | RustDesk vs NoMachine vs Guacamole for R10 compliance |
| Spike | [SPIKE-005](../../../research/Complete/(SPIKE-005)-Securing-Guacamole-on-Hub/(SPIKE-005)-Securing-Guacamole-on-Hub.md) | Securing Guacamole on Hub | Complete | Guacamole hardening: WireGuard-only binding, TOTP, TLS via DNS-01 |
| Spike | [SPIKE-006](../../../research/Complete/(SPIKE-006)-WireGuard-Fallback-Recovery/(SPIKE-006)-WireGuard-Fallback-Recovery.md) | WireGuard Fallback & Recovery | Complete | Five-layer recovery model: watchdog, reverse SSH, SMS, RustDesk, OS-level |
| Spike | [SPIKE-007](../../../research/Complete/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility/(SPIKE-007)-Ephemeral-VPS-Hub-Feasibility.md) | Ephemeral VPS Hub Feasibility | Complete | Ephemeral vs always-on hub; DNS endpoint strategy; rebuild-from-repo model |
| ADR | [ADR-001](../../../adr/Superseded/(ADR-001)-RustDesk-for-Remote-Desktop.md) | RustDesk for Remote Desktop | Superseded | Superseded by ADR-005 (Guacamole gateway model) |
| ADR | [ADR-003](../../../adr/Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md) | Network Layer for Remote Fleet | Abandoned | Evaluated Tailscale vs ZeroTier vs WireGuard; superseded by ADR-004 |
| ADR | [ADR-004](../../../adr/Superseded/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) | WireGuard Hub-and-Spoke Relay | Superseded | Self-hosted WireGuard via VPS; superseded by ADR-008 |
| ADR | [ADR-008](../../../adr/Adopted/(ADR-008)-Nebula-Overlay-Network.md) | Nebula Overlay Network | Adopted | Certificate-based overlay; replaces WireGuard (ADR-004) |
| ADR | [ADR-005](../../../adr/Adopted/(ADR-005)-Remote-Desktop-Access-Model.md) | Remote Desktop Access Model | Adopted | Guacamole gateway + native protocols; replaces ADR-001 |
| Spec | [SPEC-002](../../../spec/Deprecated/(SPEC-002)-Remote-Desktop/(SPEC-002)-Remote-Desktop.md) | Remote Desktop Bootstrap | Deprecated | ADR-005 supersedes RustDesk with Guacamole + native protocols |
| Spec | [SPEC-003](../../../spec/Implemented/(SPEC-003)-WireGuard-Hub-and-Mesh-Network/(SPEC-003)-WireGuard-Hub-and-Mesh-Network.md) | WireGuard Hub & Mesh Network | Implemented | porthole CLI: hub config, state schema, CoreDNS, peer enrollment |
| Spec | [SPEC-004](../../../spec/Implemented/(SPEC-004)-Guacamole-Remote-Desktop-Gateway/(SPEC-004)-Guacamole-Remote-Desktop-Gateway.md) | Guacamole Remote Desktop Gateway | Implemented | Docker Compose stack, Caddy TLS, seed-guac command |
| Spec | [SPEC-005](../../../spec/Implemented/(SPEC-005)-Node-Health-and-Recovery-Agent/(SPEC-005)-Node-Health-and-Recovery-Agent.md) | Node Health & Recovery Agent | Implemented | wg-watchdog, reverse SSH tunnel, gen-peer-scripts command |
| PRD | [PRD-004](../../../prd/Abandoned/(PRD-004)-RustDesk-Self-Hosted-Relay/(PRD-004)-RustDesk-Self-Hosted-Relay.md) | RustDesk Self-Hosted Relay | Abandoned | WireGuard mesh eliminates the need for a relay |
| Epic | [EPIC-007](../(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap.md) | Zero-Touch Hub Provisioning & Interactive Node Bootstrap | Proposed | Terraform + Ansible for hub IaC; Textual TUI for node enrollment |

## Key dependencies

- **ADR-008 (Adopted):** Nebula overlay network is the chosen network layer,
  superseding ADR-004 (WireGuard hub-and-spoke). Certificate-based enrollment
  solves spoke N+1 without SSH; group-based firewall for role-appropriate access.
- **ADR-005 (Adopted):** Guacamole gateway + native protocols replaces RustDesk
  as the remote desktop model. SPEC-002 (RustDesk install) is now Deprecated.

## Key decisions pending

1. **Family machine onboarding model**: How do non-technical family members
   set up and maintain the Nebula client on their machines?

## Key decisions resolved

2. **Repo boundary** (settled by EPIC-007): The fleet agent (WireGuard +
   service files) lives in this repo. The node bootstrap TUI (`setup.sh` →
   Textual app) is the single entry point for all machine types — workstations,
   servers, and family machines alike. It detects the platform and role, and
   installs only what is appropriate. No separate repo is needed.

3. **Guacamole deployment** (settled by [SPIKE-005](../../../research/Complete/(SPIKE-005)-Securing-Guacamole-on-Hub/(SPIKE-005)-Securing-Guacamole-on-Hub.md)):
   Guacamole runs on the VPS hub, bound to the Nebula interface
   (10.100.0.1) so it is only reachable from within the overlay. TLS via DNS-01
   (Cloudflare). Auth: database + TOTP, with TOTP bypass for the Nebula
   subnet.
