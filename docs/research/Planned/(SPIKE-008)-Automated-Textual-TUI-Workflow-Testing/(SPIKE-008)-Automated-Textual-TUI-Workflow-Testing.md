---
title: "Automated Textual TUI Workflow Testing"
artifact: SPIKE-008
status: Planned
author: cristos
created: 2026-03-05
last-updated: 2026-03-05
question: "Can Textual TUI workflows be tested end-to-end with automated tooling analogous to Playwright or Cypress for web apps — walking through multi-screen flows, asserting screen content, and simulating user input?"
gate: "Pre-fix for BUG-001"
risks-addressed:
  - "Regression risk: TUI changes break enrollment flow with no automated detection"
  - "BUG-001 recurrence: error states and dead-end screens go unnoticed without workflow-level tests"
depends-on: []
---

# SPIKE-008: Automated Textual TUI Workflow Testing

## Question

Can Textual TUI workflows be tested end-to-end with automated tooling analogous to
Playwright or Cypress for web apps — walking through multi-screen flows, asserting
screen content, and simulating user input?

Specifically:

1. **Textual's built-in testing**: Textual provides a `pilot` testing API and
   snapshot testing. How far does this go for multi-screen workflow testing? Can it
   simulate a full enrollment flow (Prerequisites -> Secrets -> Hub Check -> Enroll)?
2. **External TUI testing tools**: Are there tools like `pexpect`, `tmux send-keys`,
   or dedicated TUI testing frameworks that can drive a Textual app from the outside?
3. **CI integration**: Can these tests run headlessly in CI (GitHub Actions) without
   a real terminal?
4. **Mock boundaries**: What needs to be mocked (system commands, network, SOPS
   decrypt) vs. what can run for real in a test harness?

## Go / No-Go Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Multi-screen flow | A single test walks through at least 3 TUI screens in sequence, asserting content at each step | Cannot advance past a single screen programmatically |
| User input simulation | Test can click buttons, type text, and press keys | Input simulation is unreliable or requires real terminal |
| Error state assertion | Test can verify that a failed prerequisite shows the correct error message and disables Continue | Cannot inspect widget state after a simulated failure |
| CI-compatible | Tests pass in GitHub Actions without a real TTY | Requires a real terminal or X11 display |

## Pivot Recommendation

If Textual's `pilot` API cannot handle multi-screen flows reliably, fall back to
**snapshot testing per screen** (Textual's built-in SVG snapshots) combined with
**unit tests for screen transition logic** (test the state machine, not the rendered
UI). This gives partial coverage without full workflow automation.

If no automated approach is viable, establish a **manual test script** (checklist in
RUNBOOK-001) that the operator runs after TUI changes, and accept the regression risk.

## Findings

_To be populated during Active phase._

### Areas to investigate

- [`textual.pilot`](https://textual.textualize.io/guide/testing/) — Textual's
  official testing API. Supports `click()`, `press()`, `type()`, and assertions on
  widget content. Used with `pytest` and `App.run_test()`.
- Textual snapshot testing — SVG-based golden-file comparisons for visual regression.
- `pytest-textual-snapshot` — Community plugin for snapshot workflows.
- `pexpect` / `ptyprocess` — Process-level TUI driving (useful for black-box testing
  of the `setup.sh` entry point).
- Mocking patterns for `subprocess.run`, `shutil.which`, and SOPS operations in the
  context of Textual test harnesses.

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Planned | 2026-03-05 | _pending_ | Created to support BUG-001 fix and prevent TUI regression |
