---
artifact: SPEC-007
title: Operator Dashboard
status: Implemented
author: cristos
created: 2026-03-03
last-updated: 2026-03-03
parent-epic: EPIC-004
linked-research: []
linked-adrs: []
depends-on:
  - SPEC-003
---

# SPEC-007: Operator Dashboard

**Status:** Implemented
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [(EPIC-004) Operator Dashboard](../../../epic/Proposed/(EPIC-004)-Operator-Dashboard/(EPIC-004)-Operator-Dashboard.md)
**Depends on:** [SPEC-003](../Implemented/(SPEC-003)-WireGuard-Hub-and-Mesh-Network/(SPEC-003)-WireGuard-Hub-and-Mesh-Network.md) (WireGuard + SSH state must exist)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-03 | 722deda | Initial creation; implementing immediately |
| Implemented | 2026-03-03 | 6738203 | wgmesh dashboard command, port 8080 |

---

## Problem Statement

The operator needs a quick visual overview of all fleet peers — last seen,
connected/stale/offline status, transfer stats — without opening a terminal.
The existing `wgmesh status` CLI is powerful but requires SSH context and
text parsing.

## External Behavior

After this spec is implemented:

1. `wgmesh dashboard` starts a local HTTP server on `0.0.0.0:8080`.
2. Opening `http://localhost:8080/` shows a dashboard with all fleet peers,
   including: name, WireGuard IP, DNS name, last handshake (age), Tx/Rx,
   endpoint, and connected/stale/offline indicator.
3. `GET /api/status` returns JSON peer data (fetched fresh from hub via SSH).
4. A "Refresh" button (or 60 s auto-refresh) re-fetches data from the VPS.
5. `wgmesh dashboard --port <N>` changes the listening port.

## Implementation Approach

- `src/wgmesh/commands/dashboard.py` with `run_dashboard(port)`.
- Python stdlib `http.server.BaseHTTPRequestHandler`.
- Reuses `ssh.ssh_run()` and the peer/key-map logic from `status.py`.
- Inline HTML/CSS/JS (no external deps, no template files needed).
- `/api/status` returns JSON; `/` serves the dashboard HTML that fetches
  `/api/status` and renders it client-side.
- `wgmesh dashboard` command added to `cli.py`.

## Success Criteria

- `wgmesh dashboard` starts without error and serves on port 8080.
- Dashboard page loads and shows correct fleet peer data.
- Refresh fetches fresh data from hub via SSH.
- `--port` option works.
