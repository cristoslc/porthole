---
artifact: EPIC-004
title: Operator Dashboard
status: Complete
author: cristos
created: 2026-02-28
last-updated: 2026-03-03
parent-vision: VISION-001
depends-on:
  - EPIC-002
---

# EPIC-004: Operator Dashboard

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 6405885 | Initial creation, merged from external project |
| Complete | 2026-03-03 | 6738203 | SPEC-007 implemented: porthole dashboard command on port 8080 |

---

## Goal

Give the operator a single-pane view of the entire WireGuard mesh network without requiring real-time infrastructure on the VPS. The VPS remains dumb — a script generates a JSON status file on demand, and the dashboard pulls and renders it. The dashboard runs on the operator's homelab alongside existing services.

## Success criteria

- Dashboard displays all peers with last-seen time, transfer stats, and up/down status from a single view.
- Data is refreshed on demand (not real-time) by pulling a status snapshot from the VPS.
- Dashboard runs on the operator's homelab as a container or service.
- No persistent connection or agent required on the VPS beyond the existing status script.

## Scope boundaries

**In scope:**

- Web UI (Node.js) running on operator's homelab
- On-demand status refresh: SSH to VPS → run status script → parse JSON → render
- Peer list with: name, DNS name, IP, last handshake, transfer RX/TX, connected/stale/offline indicator
- Historical tracking is a stretch goal — initial version is point-in-time snapshot only

**Out of scope:**

- Real-time WebSocket updates or push notifications
- Alerting (Uptime Kuma or similar covers this separately)
- Peer provisioning from the dashboard (CLI in EPIC-002)
- Any services or daemons running on the VPS beyond the existing WireGuard + CoreDNS + status script

## Child artifacts

| Type | ID | Title | Status | Notes |
|------|----|-------|--------|-------|
| Spec | [SPEC-007](../../spec/Implemented/(SPEC-007)-Operator-Dashboard/(SPEC-007)-Operator-Dashboard.md) | Operator Dashboard | Implemented | porthole dashboard command; Python stdlib HTTP server; /api/status JSON |

## Key dependencies

- EPIC-002 for the VPS status script (`vps-status.sh`) and network state file
- SSH access from the homelab to the VPS
