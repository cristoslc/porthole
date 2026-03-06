# Agent Spec Lifecycle Index

## Draft

_No specs in this phase._

## Review

_No specs in this phase._

## Approved

_No specs in this phase._

## Implemented

| ID | Title | Author | Created | Last Updated | Commit | Notes |
|----|-------|--------|---------|--------------|--------|-------|
| SPEC-010 | TUI Navigation and Lifecycle Tests | cristos | 2026-03-05 | 2026-03-05 | e471800 | 23 tests pass, production fixes included |
| SPEC-009 | Node Bootstrap TUI | cristos | 2026-03-03 | 2026-03-04 | 32f5763 | All 5 screens + --check flag complete |
| SPEC-008 | Hub Infrastructure as Code | cristos | 2026-03-03 | 2026-03-04 | e56f0ee | backend.tf (both providers), DO firewall ports, Guacamole schema init + seed exec + platform template, guacamole_db_password |
| SPEC-003 | WireGuard Hub & Mesh Network | cristos | 2026-03-03 | 2026-03-04 | 031aaaa | porthole CLI implements all templates, state schema, modules; adds platform field, peer-config, install-peer |
| SPEC-004 | Guacamole Remote Desktop Gateway | cristos | 2026-03-03 | 2026-03-04 | 031aaaa | Docker Compose stack, Caddy TLS, seed-guac command; adds admin password in state, --apply flag |
| SPEC-005 | Node Health & Recovery Agent | cristos | 2026-03-03 | 2026-03-04 | 031aaaa | wg-watchdog, reverse SSH tunnel, gen-peer-scripts; notes Windows watchdog code gap; adds reconnect event logging |
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
