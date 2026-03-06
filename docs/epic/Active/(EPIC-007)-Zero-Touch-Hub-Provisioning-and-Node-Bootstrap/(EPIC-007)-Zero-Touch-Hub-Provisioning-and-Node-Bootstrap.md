---
title: "Zero-Touch Hub Provisioning & Interactive Node Bootstrap"
artifact: EPIC-007
status: Active
author: cristos
created: 2026-03-03
last-updated: 2026-03-03
parent-vision: VISION-001
success-criteria:
  - Destroying and rebuilding the hub VPS from scratch produces an identical working hub with no manual steps beyond `terraform apply && ansible-playbook site.yml`.
  - Running `./setup.sh` on a fresh Linux Mint or macOS machine walks the user through full node enrollment with no prior knowledge of porthole or WireGuard.
  - Running `./setup.sh` on an already-enrolled machine is safe and idempotent — it detects existing state and offers only relevant actions.
  - Secrets (age key, network state) are generated on first run and never re-created unless the user explicitly requests regeneration.
  - The hub spin-up path (Terraform + Ansible) is reachable from the TUI when the hub is not detected.
depends-on: []
---

# EPIC-007: Zero-Touch Hub Provisioning & Interactive Node Bootstrap

**Status:** Active
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-03-03 | 2ec07f7 | Initial creation — architectural direction established |
| Active | 2026-03-03 | 5719c48 | Implementation begins — SPEC-008 and SPEC-009 tasks ready |

---

## Goal / Objective

Make the hub fully rebuildable from code (Terraform + Ansible, no manual SSH) and
make node enrollment a single-command guided experience (Textual TUI). Together,
these eliminate the two biggest sources of manual toil: standing up the hub and
enrolling a new node.

The existing `porthole bootstrap` command (SSH-executed shell scripts) served as a
proof-of-concept. This epic replaces it with proper IaC and a user-facing
interactive bootstrap wizard modeled on the
[202602-workstation](https://github.com/cristoslc/202602-workstation) pattern:
a `setup.sh` bash shim that invokes a uv-managed Textual TUI.

## Scope Boundaries

**In scope:**

- Terraform configuration for hub VPS lifecycle (provision, DNS records, firewall rules).
- Ansible playbook for hub configuration (WireGuard, CoreDNS, nftables, Guacamole, Caddy, tunnel user).
- `setup.sh` entry point for nodes: bash shim → Textual TUI.
- TUI flows for: prerequisite installation (Linux Mint and macOS), secret
  management (age key + network state), hub availability check, hub spin-up,
  and node enrollment (porthole add + sync + service file installation).
- Idempotency throughout: re-running setup on an already-enrolled machine must
  be safe and informative, not destructive.
- Secret regeneration: TUI offers to re-generate age key or re-initialize network
  state on demand, with explicit confirmation.

**Out of scope:**

- Windows provisioning automation (documented manual steps remain acceptable).
- Multi-provider Terraform abstraction (one reference provider is sufficient).
- Full Ansible inventory management for non-hub nodes (node config is handled by
  porthole CLI + service file templates, not Ansible).
- TUI theming or branding beyond functional clarity.

## Child Specs

| Type | ID | Title | Status |
|------|----|-------|--------|
| Spec | [SPEC-008](../../../spec/Implemented/(SPEC-008)-Hub-Infrastructure-as-Code/(SPEC-008)-Hub-Infrastructure-as-Code.md) | Hub Infrastructure as Code | Draft |
| Spec | [SPEC-009](../../../spec/Implemented/(SPEC-009)-Node-Bootstrap-TUI/(SPEC-009)-Node-Bootstrap-TUI.md) | Node Bootstrap TUI | Draft |

## Related Artifacts

| Type | ID | Title | Status |
|------|----|-------|--------|
| Bug | [BUG-001](../../../bug/Abandoned/(BUG-001)-TUI-Error-States-Opaque-and-Unrecoverable.md) | Node Bootstrap TUI Error States Are Opaque and Unrecoverable | Reported |
| Spike | [SPIKE-008](../../../research/Planned/(SPIKE-008)-Automated-Textual-TUI-Workflow-Testing/(SPIKE-008)-Automated-Textual-TUI-Workflow-Testing.md) | Automated Textual TUI Workflow Testing | Planned |

## Key Dependencies

- **ADR-006 (Adopted):** Hub Provisioning via Terraform + Ansible — the
  architectural decision that motivates this epic.
- **SPIKE-007 (Complete):** Ephemeral VPS Hub Feasibility — validated that the
  hub can be treated as cattle (destroy + rebuild) rather than a pet, provided
  network state is stored externally.
- **SPEC-003 (Implemented):** WireGuard Hub & Network — the porthole CLI and
  network state schema that SPEC-008 and SPEC-009 build on top of.
