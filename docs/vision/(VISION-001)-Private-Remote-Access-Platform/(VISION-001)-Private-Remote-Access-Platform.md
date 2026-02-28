# VISION-001: Remote Access for a Personal Fleet

**Status:** Draft
**Author:** cristos
**Created:** 2026-02-27
**Last Updated:** 2026-02-28

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-02-27 | d8d3270 | Initial creation from EPIC-001 |

---

## Overview

Reliable remote desktop and SSH access to ~10 machines — Linux, macOS, and Windows — including non-technical family members' machines in remote locations. The best solution is a product that does this out of the box. This project exists to find that product, or — if nothing on the market fits — to assemble one from components. See [product-landscape.md](./product-landscape.md) for the decision matrix.

## Who

- **Operator:** One technical person who administers their own machines and provides remote support to family.
- **Family members:** Non-technical. They should never have to do anything after initial setup. The system is invisible to them.

## What we need

| # | Requirement | Notes |
|---|-------------|-------|
| R1 | Remote desktop: Linux, macOS, Windows as both host and client | Must work for "help Mom with her computer" and "connect to my home lab from a hotel" |
| R2 | SSH access via stable hostnames or IPs | Direct from terminal, not through a web console |
| R3 | NAT traversal without port forwarding | Machines are behind residential NATs, carrier-grade NAT, hotel WiFi |
| R4 | Family members passive after one-time setup | Zero ongoing technical steps |
| R5 | Low maintenance for ~10 machines | One person, spare time, not a job |
| R6 | Reasonable cost for personal use | $0-20/mo, not enterprise pricing |
| R7 | Network isolation from existing infrastructure | Fleet machines shouldn't see VMs/Docker/NAS on the existing tailnet |

## What we'd like

- Polished operator experience (TUI, local dashboard) — not raw shell commands
- Automation-friendly provisioning (IaC, headless setup, CLI enrollment)
- Self-hosted fallback available for critical components
- Cross-platform automation (Linux/macOS via Ansible; Windows at least documented)

## What we don't need

- Windows provisioning automation (manual is fine)
- General fleet management (monitoring, patching, config management for family machines)
- Mobile device management
- File sync or backup
- Multi-tenant or team features

## Guiding principles

1. **Buy over build.** If a product solves this at a reasonable cost — cloud, commercial, whatever — use it. Building is the fallback, not the goal.
2. **Family-friendly is non-negotiable.** If it requires a family member to understand networking, it's disqualified.
3. **Cross-platform is non-negotiable.** Linux, macOS, and Windows are all first-class. A solution that's great on two but broken on the third doesn't count.
4. **Delight matters.** If we do build, the operator experience should feel like a product — not a pile of Ansible output.

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Epic | [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Proposed |

## Open questions

- Does an existing product or product combination score well enough on the decision matrix to adopt directly? (See [product-landscape.md](./product-landscape.md).)
- If we build: what is the right network layer? (Tracked in ADR-003 under EPIC-001.)
- If we build: should the fleet agent live in a separate repo from the workstation bootstrapper?
- What is the family onboarding model — fully automated agent install, or guided manual setup?
