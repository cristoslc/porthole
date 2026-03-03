# VISION-001: Remote Access for a Personal Fleet

**Status:** Active
**Author:** cristos
**Created:** 2026-02-27
**Last Updated:** 2026-03-02

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-02-27 | d8d3270 | Initial creation from EPIC-001 |
| Active | 2026-03-02 | aad1d3a | Research complete, ADRs adopted, epics defined |

---

## Overview

A bootstrap that turns any Linux server, Linux workstation, macOS workstation, or Windows workstation into a node in a private remote-access network. Run it on a machine, and that machine becomes reachable — via SSH, remote desktop, or both — from every other node in the fleet.

The operator manages ~10 machines across homes and remote family locations. Today, setting up remote access means manually installing VPN clients, configuring SSH keys, installing remote desktop tools, and remembering which machine is at which IP. Every new machine repeats this work. Every network change breaks something.

After the bootstrap: machines find each other automatically, connections traverse NATs without port forwarding, and access is configured appropriately for each machine's role — SSH for servers, SSH plus remote desktop for workstations.

## Who

- **Operator:** One technical person who administers their own machines and provides remote support to family.
- **Family members:** Non-technical. They should never have to do anything after initial setup. The system is invisible to them.

## What we need

| # | Requirement | Notes |
|---|-------------|-------|
| R1 | Any node reaches any other node | Full mesh — no hub, no single point of failure for connectivity |
| R2 | SSH access via stable hostnames | `ssh hostname` from terminal. No web consoles, no IPs to remember |
| R3 | Remote desktop for workstations | Linux, macOS, Windows as both host and client. Not needed for headless servers |
| R4 | NAT traversal without port forwarding | Machines are behind residential NATs, carrier-grade NAT, hotel WiFi |
| R5 | Network isolation | The fleet network is access-only — nodes cannot reach other infrastructure (VMs, Docker, NAS) on the same physical network |
| R6 | Family members passive after one-time setup | Zero ongoing technical steps for non-technical users |
| R7 | Automated provisioning | `make apply` (or equivalent) on Linux/macOS. Documented manual steps for Windows |
| R8 | Low maintenance for ~10 machines | One person, spare time, not a job |
| R9 | Reasonable cost | $0-20/mo, not enterprise pricing |
| R10 | Silent background operation | All agents (VPN, remote desktop) run as background services — no foreground windows, no tray icons required, no user interaction to maintain connectivity |

## What we'd like

- Polished operator experience — not raw shell commands
- Self-hosted option for critical components (services are fine if trustworthy)
- Composable: servers get networking + SSH only, workstations get networking + SSH + remote desktop

## What we don't need

- Windows provisioning automation (manual setup is fine)
- General fleet management (monitoring, patching, config management beyond access)
- Mobile device management
- File sync or backup
- Multi-tenant or team features

## Guiding principles

1. **Compose, don't build.** The bootstrap assembles best-of-breed components (mesh VPN, remote desktop tool, SSH config). It does not reinvent any of them.
2. **Family-friendly is non-negotiable.** If it requires a family member to understand networking, it's disqualified.
3. **Cross-platform is non-negotiable.** Linux, macOS, and Windows are all first-class targets. A solution that's great on two but broken on the third doesn't count.
4. **Vendor resilience over vendor avoidance.** Services are fine. What matters is that the operator isn't forced into a reactive migration when a vendor changes direction. Prefer products with self-hosted fallbacks, open protocols, or sufficient market competition.
5. **Role-appropriate access.** Servers get SSH. Workstations get SSH and remote desktop. The bootstrap knows the difference and configures accordingly.

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Epic | [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Proposed |
| Epic | [EPIC-002](../../epic/Proposed/(EPIC-002)-Provisioning-CLI/(EPIC-002)-Provisioning-CLI.md) | Provisioning CLI & Network State Management | Proposed |
| Epic | [EPIC-003](../../epic/Proposed/(EPIC-003)-Client-Web-UI/(EPIC-003)-Client-Web-UI.md) | Client Node Web UI | Proposed |
| Epic | [EPIC-004](../../epic/Proposed/(EPIC-004)-Operator-Dashboard/(EPIC-004)-Operator-Dashboard.md) | Operator Dashboard | Proposed |
| Epic | [EPIC-005](../../epic/Proposed/(EPIC-005)-VPS-Bootstrap/(EPIC-005)-VPS-Bootstrap.md) | VPS Bootstrap & Disaster Recovery | Proposed |
| Epic | [EPIC-006](../../epic/Proposed/(EPIC-006)-Internal-DNS/(EPIC-006)-Internal-DNS.md) | Internal DNS Resolution | Proposed |
| Spike | [SPIKE-003](../../research/(SPIKE-003)-Hands-On-Validation-of-Remote-Access-Contenders/(SPIKE-003)-Hands-On-Validation-of-Remote-Access-Contenders.md) | Hands-On Validation of Remote Access Contenders | Abandoned |

## Supporting documents

| Document | Description |
|----------|-------------|
| [product-landscape.md](./product-landscape.md) | Decision matrix: desktop tools and networking bridges evaluated independently, then combinations scored against requirements |
| [wireguard-mesh-architecture.md](./wireguard-mesh-architecture.md) | Architecture overview: WireGuard hub-and-spoke relay via VPS, SOPS/age state management, CoreDNS |
