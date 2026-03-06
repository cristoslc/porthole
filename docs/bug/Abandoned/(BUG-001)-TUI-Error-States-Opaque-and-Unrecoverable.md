---
title: "Node Bootstrap TUI Error States Are Opaque and Unrecoverable"
artifact: BUG-001
status: Abandoned
author: cristos
created: 2026-03-05
last-updated: 2026-03-05
abandoned-reason: "Specious — bootstrap should install prereqs automatically, not present pass/fail checks"
severity: high
affected-artifacts:
  - SPEC-009
  - EPIC-007
discovered-in: "JOURNEY-002 walkthrough — running ./setup.sh on a fresh node"
fix-ref: "iac-remote-desktop-node-3b9"
depends-on: []
---

# BUG-001: Node Bootstrap TUI Error States Are Opaque and Unrecoverable

## Description

When running `./setup.sh` on a new node, the Node Bootstrap TUI (SPEC-009) enters
failure states that are unusable: the **Continue** button is non-functional, failed
checks show an `[x]` indicator with no explanation of what went wrong, there is no
guidance on how to remediate failures, and there is no clear way to quit the TUI.

The operator is stranded in a broken screen with no path forward, no path back, and
no way out.

## Reproduction Steps

1. Check out the repo on a fresh Linux node that has not been enrolled.
2. Run `./setup.sh`.
3. Proceed through the TUI until a prerequisite check fails (e.g., Terraform).
4. Observe the `[x]` next to the failed check.
5. Attempt to click **Continue**.
6. Attempt to find any remediation guidance or quit mechanism.

## Expected Behavior

- Failed checks should display a human-readable explanation of what failed and why.
- The TUI should suggest remediation steps (e.g., "Install Terraform: `sudo apt install terraform`" or a link to docs).
- **Continue** should either be disabled until all checks pass, or should proceed with a warning and explanation of consequences.
- There should always be a clear way to quit (e.g., `q` keybinding, visible Quit button, or `Ctrl+C` handling).

## Actual Behavior

- `[x]` next to Terraform with no explanation of what it means or what failed.
- **Continue** button is present but non-functional — clicking it does nothing.
- No remediation guidance is shown anywhere on the screen.
- No obvious way to exit the TUI. The operator is trapped.

## Impact

This is the **first-run experience** for every new node enrollment. An operator
encountering this on a fresh machine has no way to complete setup through the TUI
and must `Ctrl+C` kill the process, then figure out what to do from scratch. This
undermines the entire purpose of the guided bootstrap TUI (SPEC-009) and makes
JOURNEY-002 Stage 2 (Prerequisites) a dead end.

## Root Cause Analysis

Six code gaps across the TUI produce the three reported symptoms:

| Gap | File | Line(s) | Issue |
|-----|------|---------|-------|
| **#1** | `screens/prerequisites.py` | 82 | Continue button `disabled=not all_ok` — correctly disabled, but **no message** explaining why |
| **#2** | `screens/prerequisites.py` | 86-91 | Failed rows render `[x] terraform` — no `(not installed)` detail or context |
| **#3** | `screens/prerequisites.py` | 17-25 | Install commands exist in `platform.py` but are never shown to the operator before clicking Install |
| **#4** | `app.py` | PortholeApp class | No `BINDINGS`, no `action_quit`, no Footer help text — operator is trapped |
| **#5** | All screens | secrets.py:170, hub_check.py:64-74, hub_spinup.py:210-215 | Error messages only appear in RichLog after user action — no persistent validation banner |
| **#6** | `app.py` | PortholeApp class | No `Ctrl+C` / graceful shutdown handler |

All paths are relative to `src/porthole_setup/`.

### Symptom-to-gap mapping

- **Continue non-functional:** Gap #1 — button is disabled (correct) but no explanation shown (broken UX)
- **`[x]` with no explanation:** Gaps #2 + #3 — no detail text, no remediation
- **No way to quit:** Gaps #4 + #6 — no bindings, no handler

### Fix approach

1. Add global quit binding + Footer help to `PortholeApp` (Gaps #4, #6)
2. Add error detail + remediation text to failed prerequisite rows (Gaps #2, #3)
3. Add validation banner widget explaining disabled Continue state (Gap #1)
4. Repeat validation banner pattern across Secrets, Hub Check, Hub Spinup, Summary screens (Gap #5)

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Reported | 2026-03-05 | 6c746d4 | Discovered during fresh-node enrollment walkthrough |
| Active | 2026-03-05 | d1bf23a | Root-caused: 6 code gaps; fix approach defined |
| Abandoned | 2026-03-05 | 7209b5b | Specious — bootstrap should install prereqs, not present pass/fail checks |
