# ADR Lifecycle Index

## Adopted

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-004](Adopted/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) | WireGuard Hub-and-Spoke Relay | Adopted WireGuard hub-and-spoke relay via VPS for NAT traversal across the personal fleet. | 2026-02-28 | d69e12e |
| [ADR-005](Adopted/(ADR-005)-Remote-Desktop-Access-Model.md) | Remote Desktop Access Model | Adopted Guacamole gateway model for remote desktop, superseding RustDesk (ADR-001) based on R10 compliance and WireGuard network. | 2026-02-28 | 6d1cb09 |
| [ADR-006](Adopted/(ADR-006)-Hub-Provisioning-via-Terraform-and-Ansible.md) | Hub Provisioning via Terraform and Ansible | Adopted Terraform and Ansible for hub provisioning, capturing the architectural direction for EPIC-007. | 2026-03-03 | 2ec07f7 |

## Superseded

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-001](Superseded/(ADR-001)-RustDesk-for-Remote-Desktop.md) | RustDesk for Remote Desktop | Originally adopted RustDesk for remote desktop; superseded by ADR-005 (Guacamole gateway model). | 2026-02-28 | 6d1cb09 |

## Abandoned

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [ADR-003](Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md) | Network Layer for Remote Fleet | Proposed Tailscale ACLs for network layer; abandoned in favor of ADR-004 (WireGuard hub-and-spoke). | 2026-02-28 | d69e12e |

---

### Unassigned numbers

| ID | Reason |
|----|--------|
| ADR-002 | Number was not assigned. No artifact was created with this ID. |
