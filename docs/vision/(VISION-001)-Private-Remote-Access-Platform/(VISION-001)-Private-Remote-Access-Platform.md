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

Reliable remote desktop and SSH access to ~10 machines — Linux, macOS, and Windows — including non-technical family members' machines in remote locations.

The solution has two independent dimensions:

1. **Remote desktop** — which tool streams the desktop?
2. **Networking bridge** — how do machines find and reach each other across NATs, and how does the operator get SSH?

Some products bundle both (TeamViewer, MeshCentral); others are components that compose (NoMachine + Tailscale, RustDesk + Tailscale). The [product landscape](./product-landscape.md) evaluates each dimension independently, then scores every valid combination against the requirements below.

The best outcome is adopting an existing product or combination. This project exists to find it. If nothing fits, the fallback is building glue between best-of-breed components.

**Context:** The operator currently uses Remotix (NEAR protocol), which was acquired by Acronis and rebranded as Acronis Cyber Protect Connect. The product's direction is uncertain under new ownership — subscription-only pricing, unclear on-prem future, sparse documentation. This motivates a systematic evaluation before being forced to migrate reactively.

## Who

- **Operator:** One technical person who administers their own machines and provides remote support to family.
- **Family members:** Non-technical. They should never have to do anything after initial setup. The system is invisible to them.

## What we need

| # | Requirement | Dimension | Notes |
|---|-------------|-----------|-------|
| R1 | Remote desktop: Linux, macOS, Windows as both host and client | Desktop | Must work for "help Mom with her computer" and "connect to my home lab from a hotel" |
| R2 | SSH access via stable hostnames or IPs | Network | Direct from terminal, not through a web console |
| R3 | NAT traversal without port forwarding | Network | Machines are behind residential NATs, carrier-grade NAT, hotel WiFi |
| R4 | Family members passive after one-time setup | Both | Zero ongoing technical steps |
| R5 | Low maintenance for ~10 machines | Both | One person, spare time, not a job |
| R6 | Reasonable cost for personal use | Both | $0-20/mo, not enterprise pricing |
| R7 | Network isolation from existing infrastructure | Network | Fleet machines shouldn't see VMs/Docker/NAS on the existing tailnet |

## What we'd like

- Polished operator experience (Textual TUI, local web dashboard) — not raw shell commands
- Automation-friendly provisioning (IaC, headless setup, CLI enrollment)
- Self-hosted option available for critical components (not required — services are fine if trustworthy)
- Cross-platform automation (Linux/macOS via Ansible; Windows at least documented)

## What we don't need

- Windows provisioning automation (manual is fine)
- General fleet management (monitoring, patching, config management for family machines)
- Mobile device management
- File sync or backup
- Multi-tenant or team features

## Guiding principles

1. **Buy over build.** If a product solves this at a reasonable cost — cloud, commercial, self-hosted, whatever — adopt it. Building is the fallback, not the goal. The best outcome is discovering there's nothing to build.
2. **Family-friendly is non-negotiable.** If it requires a family member to understand networking, it's disqualified.
3. **Cross-platform is non-negotiable.** Linux, macOS, and Windows are all first-class. A solution that's great on two but broken on the third doesn't count.
4. **Vendor resilience over vendor avoidance.** Services are fine. What matters is that the operator isn't forced into a reactive migration when a vendor changes direction (as happened with Remotix → Acronis). Prefer products with self-hosted fallbacks, open protocols, or sufficient market competition.
5. **Delight matters.** If we do build, the operator experience should feel like a product — a Textual TUI or local web dashboard with clear state and one-click actions, not a pile of Ansible output.

## Current state

The [product landscape](./product-landscape.md) evaluation reached two conclusions:

**Networking is settled on paper: Tailscale.** Free, covers SSH (R2) + NAT traversal (R3) + isolation (R7), works with any desktop tool. NoMachine Network is strictly inferior (NM-only, no SSH, no isolation, costs $84.50/yr). Needs hands-on validation of ACL isolation and family onboarding.

**Desktop is the open question: NoMachine vs RustDesk.** Both pair with Tailscale. Both score 7Y — same R4 (two apps installed once, both passive after setup) and same R5 (both auto-update, no config management for basic operation). The requirements matrix doesn't differentiate them; the difference is purely desktop quality and UX (NX protocol vs. RustDesk native client), which requires hands-on testing.

**Custom automation is orthogonal.** Adding Ansible playbooks and an operator UI is an optional enhancement to *either* combo. It improves the operator experience but adds maintenance (R5 → P). This decision comes after choosing a desktop tool, not before.

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Epic | [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Proposed |

## Supporting documents

| Document | Description |
|----------|-------------|
| [product-landscape.md](./product-landscape.md) | Two-dimensional evaluation: desktop tools and networking bridges scored independently, then combinations scored against R1-R7 |

## Open questions

- **NoMachine vs RustDesk:** Which desktop tool feels better over Tailscale? NX protocol (compression, dated UI) vs. RustDesk native client (modern UI, fast networks). Hands-on testing required — the requirements matrix can't differentiate them.
- **Custom automation — worth the maintenance?** Adding Ansible + operator UI to either combo improves the experience but commits to ongoing upkeep. Decide after the base combo is proven.
- If we build: should the fleet agent live in a separate repo from the workstation bootstrapper?
- What is the family onboarding model — fully automated agent install, or guided manual setup?
