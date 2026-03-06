---
artifact: VISION-001
title: Remote Access for a Personal Fleet
status: Active
author: cristos
created: 2026-02-27
last-updated: 2026-03-03
depends-on: []
---

# VISION-001: Remote Access for a Personal Fleet

**Status:** Active
**Author:** cristos
**Created:** 2026-02-27
**Last Updated:** 2026-03-03

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-02-27 | d8d3270 | Initial creation from EPIC-001 |
| Active | 2026-03-02 | aad1d3a | Research complete, ADRs adopted, epics defined |

---

## Overview

Porthole is a hub-and-spoke remote access system for a personal fleet of ~10
machines — Linux workstations, macOS laptops, headless servers, and family
members' computers spread across homes and remote locations.

A lightweight VPS acts as the hub: it runs a WireGuard server, a CoreDNS
resolver, an nftables firewall, and a Guacamole remote desktop gateway. Every
node in the fleet connects to the hub over WireGuard and is reachable from
every other node via a stable `<name>.wg` hostname, through NAT, without port
forwarding. SSH and remote desktop work the same way from anywhere.

The hub is provisioned entirely from code (Terraform + Ansible) and is
designed to be disposable — if it dies, clone the repo, run two commands, and
the fleet is back. Nodes are enrolled via a single guided script (`./setup.sh`)
that installs prerequisites, manages secrets, checks hub availability, and
configures background services. Once enrolled, a node requires no ongoing
attention from the operator and nothing from a family member.

## Who

- **Operator:** One technical person who administers their own machines and
  provides remote support to family. Does the initial setup of the hub and each
  node. After that, the system runs itself.
- **Family members:** Non-technical. They never interact with the network
  directly. Their machine is enrolled once by the operator; after that it is
  invisible to them.

## What we need

| # | Requirement | Notes |
|---|-------------|-------|
| R1 | Any node reaches any other node | Traffic routes through the hub relay — no port forwarding, no static IPs required on nodes |
| R2 | SSH access via stable hostnames | `ssh name.wg` from any node. No web consoles, no IPs to remember |
| R3 | Remote desktop for workstations | Via Guacamole gateway on the hub. Linux, macOS, Windows as targets. Not needed for headless servers |
| R4 | NAT traversal without port forwarding | Nodes are behind residential NATs, carrier-grade NAT, hotel WiFi — the hub relay handles traversal |
| R5 | Network isolation | The fleet network is access-only — nodes cannot reach other infrastructure (VMs, Docker, NAS) on the same physical network |
| R6 | Family members passive after one-time setup | Zero ongoing technical steps for non-technical users |
| R7 | Automated provisioning | `./setup.sh` (Textual TUI) on Linux Mint/macOS: installs prereqs, manages secrets, checks hub, enrolls node. Documented manual steps for Windows |
| R8 | Low maintenance for ~10 machines | One person, spare time, not a job |
| R9 | Reasonable cost | $0–20/mo, not enterprise pricing |
| R10 | Silent background operation | All services (WireGuard, remote desktop, watchdog, reverse tunnel) run as background daemons — no foreground windows, no user interaction to maintain connectivity |

## What we'd like

- Polished operator experience — guided TUI for setup, not raw commands
- Hub fully rebuildable from repo state with no manual steps
- Composable: servers get networking + SSH only, workstations get networking + SSH + remote desktop
- Self-hosted for all critical components

## What we don't need

- Windows provisioning automation (manual setup is fine)
- General fleet management (monitoring, patching, config management beyond access)
- Mobile device management
- File sync or backup
- Multi-tenant or team features
- Full peer-to-peer mesh (the hub relay is sufficient; direct peering is not required)

## Guiding principles

1. **Compose, don't build.** Porthole assembles best-of-breed components
   (WireGuard, Guacamole, CoreDNS, Terraform, Ansible). It does not reinvent
   any of them.
2. **Family-friendly is non-negotiable.** If it requires a family member to
   understand networking, it is disqualified.
3. **Cross-platform is non-negotiable.** Linux, macOS, and Windows are all
   first-class targets. A solution that works on two but is broken on the third
   does not qualify.
4. **Vendor resilience over vendor avoidance.** Services are fine. What matters
   is that the operator is not forced into a reactive migration when a vendor
   changes direction. Prefer open protocols, self-hosted options, or tools with
   sufficient market competition.
5. **Role-appropriate access.** Servers get SSH. Workstations get SSH and
   remote desktop. The bootstrap configures each node for its role.
6. **Hub as cattle, not pet.** The hub VPS is disposable infrastructure.
   All persistent state lives in `network.sops.yaml`, encrypted in the repo.
   Destroying and rebuilding the hub should require no manual steps and no data
   entry beyond cloud credentials.

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Journey | [JOURNEY-001](../../journey/(JOURNEY-001)-Operator-Spins-Up-Hub/(JOURNEY-001)-Operator-Spins-Up-Hub.md) | Operator Spins Up a Fresh Hub | Draft |
| Journey | [JOURNEY-002](../../journey/(JOURNEY-002)-Operator-Enrolls-a-Node/(JOURNEY-002)-Operator-Enrolls-a-Node.md) | Operator Enrolls a Linux or macOS Node | Draft |
| Journey | [JOURNEY-003](../../journey/(JOURNEY-003)-Operator-Enrolls-a-Windows-Family-Machine/(JOURNEY-003)-Operator-Enrolls-a-Windows-Family-Machine.md) | Operator Enrolls a Windows Family Machine | Draft |
| Journey | [JOURNEY-004](../../journey/(JOURNEY-004)-Hub-Disaster-Recovery/(JOURNEY-004)-Hub-Disaster-Recovery.md) | Hub Disaster Recovery | Draft |
| Epic | [EPIC-001](../../epic/Active/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Active |
| Epic | [EPIC-002](../../epic/Complete/(EPIC-002)-Provisioning-CLI/(EPIC-002)-Provisioning-CLI.md) | Provisioning CLI & Network State Management | Complete |
| Epic | [EPIC-003](../../epic/Complete/(EPIC-003)-Client-Web-UI/(EPIC-003)-Client-Web-UI.md) | Client Node Web UI | Complete |
| Epic | [EPIC-004](../../epic/Complete/(EPIC-004)-Operator-Dashboard/(EPIC-004)-Operator-Dashboard.md) | Operator Dashboard | Complete |
| Epic | [EPIC-005](../../epic/Complete/(EPIC-005)-VPS-Bootstrap/(EPIC-005)-VPS-Bootstrap.md) | VPS Bootstrap & Disaster Recovery | Complete |
| Epic | [EPIC-006](../../epic/Abandoned/(EPIC-006)-Homelab-Service-Exposure/(EPIC-006)-Homelab-Service-Exposure.md) | Homelab Service Exposure | Abandoned |
| Epic | [EPIC-007](../../epic/Active/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap.md) | Zero-Touch Hub Provisioning & Interactive Node Bootstrap | Proposed |
| Spike | [SPIKE-003](../../research/(SPIKE-003)-Hands-On-Validation-of-Remote-Access-Contenders/(SPIKE-003)-Hands-On-Validation-of-Remote-Access-Contenders.md) | Hands-On Validation of Remote Access Contenders | Abandoned |

## Supporting documents

| Document | Description |
|----------|-------------|
| [branding-and-style-guide.md](./branding-and-style-guide.md) | Project name (Porthole), terminology, component names, and writing conventions |
| [product-landscape.md](./product-landscape.md) | Decision matrix: desktop tools and networking bridges evaluated independently, then combinations scored against requirements |
| [wireguard-mesh-architecture.md](./wireguard-mesh-architecture.md) | Architecture overview: WireGuard hub-and-spoke relay via VPS, SOPS/age state management, CoreDNS |
