---
title: "Node Bootstrap TUI Error States Are Opaque and Unrecoverable"
artifact: BUG-001
status: Reported
author: cristos
created: 2026-03-05
last-updated: 2026-03-05
severity: high
affected-artifacts:
  - SPEC-009
  - EPIC-007
discovered-in: "JOURNEY-002 walkthrough — running ./setup.sh on a fresh node"
fix-ref: ""
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

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Reported | 2026-03-05 | _pending_ | Discovered during fresh-node enrollment walkthrough |
