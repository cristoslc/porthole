# ADR Lifecycle Index

## Adopted

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-005](Adopted/(ADR-005)-Remote-Desktop-Access-Model.md) | Remote Desktop Access Model | Adopted Guacamole gateway model for remote desktop, superseding RustDesk (ADR-001) based on R10 compliance and overlay network. | 2026-02-28 | 6d1cb09 |
| [ADR-006](Adopted/(ADR-006)-Hub-Provisioning-via-Terraform-and-Ansible.md) | Hub Provisioning via Terraform and Ansible | Adopted Terraform and Ansible for hub provisioning, capturing the architectural direction for EPIC-007. | 2026-03-03 | 2ec07f7 |
| [ADR-008](Adopted/(ADR-008)-Nebula-Overlay-Network.md) | Nebula Overlay Network | Adopt Nebula as overlay network layer, replacing WireGuard (ADR-004). Certificate-based enrollment solves spoke N+1 without SSH; group-based firewall for role-appropriate access. | 2026-03-07 | — |
| [ADR-009](Adopted/(ADR-009)-Ansible-as-Prerequisite-Bootstrap-Tool.md) | Ansible as Prerequisite Bootstrap Tool | Ansible is the only tool porthole installs directly; all other prerequisites installed via Ansible playbook for a single idempotent install path per platform. | 2026-03-07 | — |

## Superseded

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-001](Superseded/(ADR-001)-RustDesk-for-Remote-Desktop.md) | RustDesk for Remote Desktop | Originally adopted RustDesk for remote desktop; superseded by ADR-005 (Guacamole gateway model). | 2026-02-28 | 6d1cb09 |
| [ADR-004](Superseded/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) | WireGuard Hub-and-Spoke Relay | Adopted WireGuard hub-and-spoke relay via VPS; superseded by ADR-008 (Nebula overlay network). | 2026-03-07 | — |

## Abandoned

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-003](Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md) | Network Layer for Remote Fleet | Proposed Tailscale ACLs for network layer; abandoned in favor of ADR-004 (WireGuard hub-and-spoke). | 2026-02-28 | d69e12e |
| [ADR-007](Abandoned/(ADR-007)-Age-Encrypted-Setup-Key-and-Cloud-Init-Bootstrap.md) | Age-Encrypted Setup Key and Cloud-Init Bootstrap | Proposed age-encrypted SSH key for hub provisioning; abandoned — Nebula adoption (ADR-008) eliminates need for SSH-based hub management. | 2026-03-07 | — |

---

### Unassigned numbers

| ID | Reason |
|----|--------|
| ADR-002 | Number was not assigned. No artifact was created with this ID. |
