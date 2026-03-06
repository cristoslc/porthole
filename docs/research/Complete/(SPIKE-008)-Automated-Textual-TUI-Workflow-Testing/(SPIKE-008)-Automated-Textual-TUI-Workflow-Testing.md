---
title: "Automated Textual TUI Workflow Testing"
artifact: SPIKE-008
status: Complete
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

### 1. Textual Pilot API (Primary — Recommended)

Textual's built-in `pilot` API via `App.run_test()` is **fully capable** of
multi-screen flow testing. Key findings:

- **Multi-screen navigation works.** `push_screen`/`pop_screen` operate normally in
  headless mode. After triggering a screen transition via `pilot.click("#continue-btn")`,
  call `await pilot.pause()` and assert on `pilot.app.screen` (current screen) or
  `pilot.app.screen_stack` (full stack).
- **Pilot methods:** `click(selector)`, `press(*keys)`, `hover(selector)`,
  `pause(delay?)`, `wait_for_animation()`, `resize_terminal(w, h)`. Click accepts
  CSS selectors (`"#continue-btn"`), widget types (`Button`), or offset coordinates.
- **Widget assertions:** After transitions, query widgets via
  `pilot.app.query_one("#id", WidgetType)` and assert on `.disabled`, `.renderable`,
  `.has_class()`, `.display`.
- **Async worker sync:** `await pilot.app.workers.wait_for_complete()` waits for all
  `@work`-decorated methods to finish. Follow with `pilot.pause()` to drain remaining
  messages. Individual workers expose `.is_finished`, `.state`.
- **CI-compatible:** `run_test(headless=True)` is the default. No TTY or X11 needed.
  Works in GitHub Actions with zero configuration.
- **Snapshot testing:** `pytest-textual-snapshot` captures SVG screenshots for visual
  regression. Supports `run_before=` callback for navigating to a specific screen before
  capture.

**Limitation:** Pilot tests the app in-process — it does not test the CLI entry point
(`porthole-setup`), TTY allocation, or real terminal rendering.

### 2. External TUI Testing (Secondary — Smoke Tests Only)

| Tool | Textual Compat | CI Support | Maintenance | Verdict |
|------|---------------|------------|-------------|---------|
| **tmux/libtmux** | Good (real terminal emulation) | Yes (apt install tmux) | Medium | Best external option |
| **pexpect + pyte** | Poor (must parse ANSI) | Yes | High | Too much custom harness |
| **expect (TCL)** | Poor | Yes | Very high | Not viable |
| **Hecate** | Good concept | Yes | Unmaintained since 2017 | Skip |

**Recommendation:** Use tmux/libtmux for 3-5 end-to-end smoke tests covering the
happy path. These verify the shipped `porthole-setup` binary works end-to-end. Use
`libtmux`'s pytest plugin for session lifecycle management and `capture-pane` for
clean text assertions.

### 3. Mock Boundaries

Six layers of external dependencies to mock, ordered by frequency:

| Layer | Target | Mock pattern |
|-------|--------|-------------|
| L1 Platform | `is_installed`, `detect_os`, `get_install_command` | `monkeypatch.setattr` at screen import path |
| L2 State | `load_state` → `NetworkState` | Return fixture with test endpoint/peers |
| L3 Filesystem | `AGE_KEY_PATH`, `SOPS_CONFIG_PATH`, `STATE_PATH` | Redirect to `tmp_path` via monkeypatch |
| L4 Async subprocess | `asyncio.create_subprocess_exec` | `make_fake_subprocess(rc, stdout_lines)` helper |
| L5 Sync subprocess | `subprocess.run` (sops, porthole init) | `monkeypatch.setattr` with rc=0 MagicMock |
| L6 App.suspend | `App.suspend()` context manager | Patch to `contextlib.nullcontext()` |

**Key pattern:** Mock at the function boundary (`is_installed`, `load_state`), not at
the subprocess level. Monkeypatch the name *as imported in the screen module*
(e.g., `porthole_setup.screens.prerequisites.is_installed`).

**Proposed conftest fixtures:**
- `mock_all_installed` — all tools present
- `mock_network_state` — valid NetworkState for hub_check/enrollment/service_install
- `mock_subprocess_success` — no-op all subprocess calls
- `mock_suspend` — `App.suspend()` → `nullcontext()`

### 4. Concrete Test Example (3-Screen Flow)

```python
@pytest.mark.asyncio
async def test_prereqs_to_hub_check(monkeypatch):
    monkeypatch.setattr("porthole_setup.screens.prerequisites.is_installed", lambda _: True)
    monkeypatch.setattr("porthole_setup.screens.hub_check.load_state", lambda: mock_state)
    monkeypatch.setattr("asyncio.create_subprocess_exec", make_fake_subprocess(rc=0))

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(pilot.app.screen, PrerequisitesScreen)

        await pilot.click("#continue-btn")  # → SecretsScreen
        await pilot.pause()
        assert isinstance(pilot.app.screen, SecretsScreen)

        pilot.app.screen.age_ok = pilot.app.screen.sops_ok = pilot.app.screen.state_ok = True
        await pilot.pause()

        await pilot.click("#continue-btn")  # → HubCheckScreen
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(pilot.app.screen, HubCheckScreen)
        assert "hub.example.com" in str(pilot.app.query_one("#endpoint-label").renderable)
```

## Go / No-Go Verdict

**GO.** All four criteria pass:

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Multi-screen flow | **Pass** | `push_screen`/`pop_screen` work in `run_test()`. `pilot.app.screen` enables assertions after transitions. |
| User input simulation | **Pass** | `click()`, `press()`, `hover()` all work headlessly with CSS selectors. |
| Error state assertion | **Pass** | Widget `.disabled`, `.renderable`, `.has_class()` fully inspectable. Reactive state can be set and asserted. |
| CI-compatible | **Pass** | Headless by default, no TTY needed. GitHub Actions works with zero config. |

**Recommended testing strategy:**
1. **Textual Pilot + pytest** for comprehensive screen and workflow tests (primary)
2. **pytest-textual-snapshot** for visual regression on key screens
3. **tmux/libtmux** for 3-5 end-to-end smoke tests of the `porthole-setup` binary (secondary)

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Planned | 2026-03-05 | 6c746d4 | Created to support BUG-001 fix and prevent TUI regression |
