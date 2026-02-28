# VISION-001: Private Remote Access Platform

**Status:** Draft
**Author:** cristos
**Created:** 2026-02-27
**Last Updated:** 2026-02-27

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-02-27 | d8d3270 | Initial creation from EPIC-001 |

---

## Overview

Reliable remote access to a personal fleet of ~10 machines — spanning Linux, macOS, and Windows — including non-technical family members' machines in remote locations. The ideal outcome is a product that solves this out of the box. This project exists because no product currently does, so we assemble one from components (mesh VPN, remote desktop, automation). If a product emerges that covers all the requirements at a reasonable cost, adopting it and retiring this project would be a success, not a failure.

## Target audience

- **Primary operator:** A technical user who administers their own machines and provides remote support to family members.
- **Secondary users:** Non-technical family members whose machines are enrolled in the fleet. They interact with the platform passively — it should be invisible during normal use and require zero ongoing technical steps after initial setup.

## Value proposition

1. **Buy over build.** If a product solves the problem at a reasonable personal-use cost, use it — even if it's cloud-hosted, even if it's commercial. Building custom infrastructure is the fallback for gaps in the market, not a goal in itself.
2. **Reach any machine from anywhere.** Remote desktop and SSH access between any two enrolled machines within seconds, regardless of NAT topology or firewall configuration.
3. **Family-friendly operations.** Remote family machines stay reachable without requiring the family member to perform ongoing technical tasks. Initial setup is a one-time, guided process.
4. **Automation with delight.** Machine provisioning is driven by infrastructure-as-code (Ansible) behind a friendly local UI — a Textual TUI app, local web dashboard, or similar — that shows fleet state, guides first-run setup, and applies updates. The operator experience should feel polished, not like raw shell commands. Windows machines have a documented guided procedure completable in under 15 minutes.
5. **Cross-platform by default.** Linux, macOS, and Windows are first-class targets. Tool choices (network layer, remote desktop client) are made with all three platforms in mind.

## Core capabilities

| Capability | Description |
|------------|-------------|
| Mesh networking | Private overlay network connecting all fleet machines with stable addressing, NAT traversal, and network isolation from existing infrastructure. |
| Remote desktop | RustDesk-based remote desktop access over the mesh network, with optional self-hosted relay for edge cases. |
| SSH access | Terminal access to all machines via stable hostnames or IPs on the mesh network. |
| Operator UI | A local application (Textual TUI, web dashboard, or similar) that surfaces fleet state, guides first-run enrollment, and triggers updates — wrapping Ansible automation in a polished operator experience. |
| Family onboarding | Low-friction enrollment path for non-technical users' machines. |

## Success metrics

1. Any two enrolled machines establish a remote desktop session within 30 seconds.
2. SSH access works between all enrolled machines via stable hostnames or IPs.
3. Family machines remain reachable without ongoing technical intervention from family members.
4. The solution cost is reasonable for personal use (not enterprise-priced for a 10-machine fleet).
5. New Linux/macOS machine enrollment completes through the operator UI (TUI or web dashboard); Windows via documented guided procedure in under 15 minutes.
6. The remote-access network is isolated from existing infrastructure (VMs, Docker containers, other services).

## Non-goals

- **Windows provisioning automation.** Windows machines are configured manually. Ansible-on-Windows (WinRM, PowerShell DSC) is out of scope.
- **General fleet management.** Monitoring, patching, and configuration management of family machines beyond connectivity and remote desktop are out of scope.
- **Mobile device management.** Phones and tablets are not part of this fleet.
- **File sync and backup.** Covered by separate efforts for personal machines only.
- **Multi-tenant or team use.** This platform serves a single operator and their family, not an organization.

## Strategic themes

### Buy over build

The best outcome is finding a product that does all of this. Remotix was close until Acronis acquired it. TeamViewer would be fine if the cost were reasonable for personal use. MeshCentral would work if its remote desktop quality matched RustDesk. This project is a bet that the gap persists — if it closes, we should adopt the product and retire the custom stack. Vendor resilience is a secondary concern: nice to have documented fallback paths, but not worth over-engineering for.

### Simplicity for non-technical users

Family members should not need to understand networking, VPNs, or remote desktop protocols. The system should be invisible during normal use and recoverable without technical knowledge if something goes wrong.

### Infrastructure as code, operator experience as product

Machine configuration is declarative and version-controlled. Drift is corrected by re-running automation, not by manual SSH sessions. The repo is the source of truth for what a managed machine should look like. But the operator interface should feel like a product — a local TUI or web dashboard that shows fleet health, guides enrollment, and applies changes — not a wall of Ansible output.

### Cross-platform pragmatism

All three major desktop platforms are supported, but automation depth varies by platform maturity. Linux and macOS get full Ansible automation; Windows gets documented manual procedures with a path toward future automation.

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Epic | [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Proposed |

## Open questions

- What is the right network layer? (Tracked in ADR-003 under EPIC-001.)
- Should the fleet agent live in a separate repo from the workstation bootstrapper? (Pending spike under EPIC-001.)
- What is the family onboarding model — fully automated agent install, or guided manual setup? (Pending investigation under EPIC-001.)
