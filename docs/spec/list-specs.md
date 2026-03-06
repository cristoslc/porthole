# Agent Spec Lifecycle Index

## Implemented

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [SPEC-003](Implemented/(SPEC-003)-WireGuard-Hub-and-Mesh-Network/(SPEC-003)-WireGuard-Hub-and-Mesh-Network.md) | WireGuard Hub & Mesh Network | WireGuard hub-and-spoke network with porthole CLI implementing all templates, state schema, and modules including platform field and peer-config. | 2026-03-04 | d46e0d2 |
| [SPEC-004](Implemented/(SPEC-004)-Guacamole-Remote-Desktop-Gateway/(SPEC-004)-Guacamole-Remote-Desktop-Gateway.md) | Guacamole Remote Desktop Gateway | Docker Compose stack with Caddy TLS and seed-guac command for browser-based remote desktop via Guacamole on the hub. | 2026-03-04 | 068a4f5 |
| [SPEC-005](Implemented/(SPEC-005)-Node-Health-and-Recovery-Agent/(SPEC-005)-Node-Health-and-Recovery-Agent.md) | Node Health & Recovery Agent | WireGuard watchdog, reverse SSH tunnel, and gen-peer-scripts for automated node health monitoring and recovery. | 2026-03-04 | 068a4f5 |
| [SPEC-006](Implemented/(SPEC-006)-Client-Node-Status-Web-UI/(SPEC-006)-Client-Node-Status-Web-UI.md) | Client Node Status Web UI | Python stdlib HTTP server providing WireGuard status and restart button on port 8888 for each client node. | 2026-03-03 | de7cdd1 |
| [SPEC-007](Implemented/(SPEC-007)-Operator-Dashboard/(SPEC-007)-Operator-Dashboard.md) | Operator Dashboard | porthole dashboard command providing fleet status via SSH on port 8080 for the operator. | 2026-03-03 | 6738203 |
| [SPEC-008](Implemented/(SPEC-008)-Hub-Infrastructure-as-Code/(SPEC-008)-Hub-Infrastructure-as-Code.md) | Hub Infrastructure as Code | Terraform and Ansible for hub provisioning including backend.tf for both providers, DO firewall, Guacamole schema init, and guacamole_db_password. | 2026-03-04 | e56f0ee |
| [SPEC-009](Implemented/(SPEC-009)-Node-Bootstrap-TUI/(SPEC-009)-Node-Bootstrap-TUI.md) | Node Bootstrap TUI | Textual TUI for guided node enrollment with 5 screens (prerequisites, secrets, hub check, enrollment, summary) and --check flag. | 2026-03-04 | 32f5763 |
| [SPEC-010](Implemented/(SPEC-010)-TUI-Navigation-and-Lifecycle-Tests/(SPEC-010)-TUI-Navigation-and-Lifecycle-Tests.md) | TUI Navigation and Lifecycle Tests | Comprehensive test suite covering TUI navigation, back/quit behavior, and screen lifecycle with 23 tests passing plus production fixes. | 2026-03-05 | e471800 |

## Deprecated

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [SPEC-002](Deprecated/(SPEC-002)-Remote-Desktop/(SPEC-002)-Remote-Desktop.md) | Remote Desktop Bootstrap | RustDesk-based remote desktop bootstrap, deprecated after ADR-005 superseded RustDesk with Guacamole and native protocols. | 2026-02-28 | d28a5bf |

---

### Unassigned numbers

| ID | Reason |
|----|--------|
| SPEC-001 | Number was not assigned. No artifact was created with this ID. |
