# Agent Spec Lifecycle Index

## Draft

| ID | Title | Author | Created | Last Updated | Commit | Notes |
|----|-------|--------|---------|--------------|--------|-------|
| SPEC-008 | Hub Infrastructure as Code | cristos | 2026-03-03 | 2026-03-03 | 2ec07f7 | Terraform for VPS lifecycle; Ansible for hub config (WireGuard, CoreDNS, nftables, Guacamole, Caddy) |
| SPEC-009 | Node Bootstrap TUI | cristos | 2026-03-03 | 2026-03-03 | 2ec07f7 | setup.sh → Textual app; prereqs, secrets, hub check, node enrollment |

## Review

_No specs in this phase._

## Approved

_No specs in this phase._

## Implemented

| ID | Title | Author | Created | Last Updated | Commit | Notes |
|----|-------|--------|---------|--------------|--------|-------|
| SPEC-003 | WireGuard Hub & Mesh Network | cristos | 2026-03-03 | 2026-03-03 | d46e0d2 | porthole CLI implements all templates, state schema, modules |
| SPEC-004 | Guacamole Remote Desktop Gateway | cristos | 2026-03-03 | 2026-03-03 | 068a4f5 | Docker Compose stack, Caddy TLS, seed-guac command |
| SPEC-005 | Node Health & Recovery Agent | cristos | 2026-03-03 | 2026-03-03 | 068a4f5 | wg-watchdog, reverse SSH tunnel, gen-peer-scripts command |
| SPEC-006 | Client Node Status Web UI | cristos | 2026-03-03 | 2026-03-03 | de7cdd1 | Python stdlib HTTP server; wg status + restart button on port 8888 |
| SPEC-007 | Operator Dashboard | cristos | 2026-03-03 | 2026-03-03 | 6738203 | porthole dashboard command; fleet status via SSH on port 8080 |

## Deprecated

| ID | Title | Author | Created | Last Updated | Commit | Notes |
|----|-------|--------|---------|--------------|--------|-------|
| SPEC-002 | Remote Desktop Bootstrap | cristos | 2026-02-26 | 2026-02-28 | d28a5bf | ADR-005 supersedes RustDesk with Guacamole + native protocols |

## Abandoned

_No specs in this phase._

---

### Unassigned numbers

| ID | Reason |
|----|--------|
| SPEC-001 | Number was not assigned. No artifact was created with this ID. |
