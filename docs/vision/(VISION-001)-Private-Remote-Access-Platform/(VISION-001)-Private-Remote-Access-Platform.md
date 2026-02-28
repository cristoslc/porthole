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

The problem decomposes into two independent choices: a **remote desktop tool** (which product streams the desktop?) and a **networking bridge** (how do machines find and reach each other across NATs?). Some products bundle both; others are components that compose. The [product landscape](./product-landscape.md) evaluates each dimension separately, then scores every valid combination against the requirements below.

The best outcome is adopting an existing product or combination. This project exists to find it. If nothing on the market fits, then — and only then — the fallback is building glue between best-of-breed components (RustDesk + Tailscale + automation).

**Context:** The operator currently uses Remotix (NEAR protocol), which was acquired by Acronis and rebranded as Acronis Cyber Protect Connect. The product's direction is uncertain under new ownership — subscription-only pricing, unclear on-prem future, sparse documentation. This motivates a systematic evaluation of alternatives before being forced to migrate reactively.

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

## Child artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Epic | [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md) | Remote Fleet Management | Proposed |

## Supporting documents

| Document | Description |
|----------|-------------|
| [product-landscape.md](./product-landscape.md) | Two-dimensional evaluation: desktop tools and networking bridges scored independently, then combinations scored against R1-R7 |

## Open questions

- **Networking layer is settled on paper: Tailscale.** Nothing else covers SSH + NAT + isolation for free. Needs hands-on validation of ACL isolation and family onboarding.
- **Desktop tool is the open question: NoMachine vs RustDesk.** NoMachine + Tailscale scores 7Y with nothing to build. RustDesk + Tailscale scores 5Y 2P but offers better desktop UX at the cost of ongoing maintenance. The answer depends on whether NX protocol quality is good enough — which requires hands-on testing, not analysis.
- If we build (RustDesk path): should the fleet agent live in a separate repo from the workstation bootstrapper?
- What is the family onboarding model — fully automated agent install, or guided manual setup?
