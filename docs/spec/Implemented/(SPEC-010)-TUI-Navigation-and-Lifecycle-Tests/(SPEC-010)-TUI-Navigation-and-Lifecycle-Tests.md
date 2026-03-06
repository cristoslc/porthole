---
title: "TUI Navigation and Lifecycle Tests"
artifact: SPEC-010
status: Implemented
author: cristos
created: 2026-03-05
last-updated: 2026-03-05
parent-epic: EPIC-007
linked-research:
  - SPIKE-008
linked-adrs: []
depends-on:
  - SPIKE-008
addresses: []
---

# SPEC-010: TUI Navigation and Lifecycle Tests

## Problem Statement

The Porthole setup TUI has 7 screens with forward/back navigation, conditional
button states, async workers, and error handling — none of which are covered by
automated tests. SPIKE-008 confirmed that Textual's pilot API is fully capable
of testing these flows headlessly. This spec adds a comprehensive test suite
covering navigation, back/quit behavior, and screen lifecycle across the entire
wizard.

An audit of the current screens reveals two navigation gaps that the tests will
expose and that must be fixed as part of this work:

1. **SecretsScreen has no Back button** — the user can navigate forward from
   Prerequisites but cannot return without quitting the app.
2. **No global quit binding** — there is no way to exit the app from any screen
   except the Summary screen's Finish button.

## External Behavior

### Navigation map (current)

```
Prerequisites ──Continue──> Secrets ──Continue──> HubCheck ──Continue──> Enrollment ──Continue──> ServiceInstall ──Continue──> Summary ──Finish──> exit
                                                    │   ↑                    │   ↑                    │   ↑                   │   ↑
                                                    │   │                    │   │                    │   │                   │   │
                                                  Back  │                  Back  │                  Back  │                 Back  │
                                                    │   │                    │   │                    │   │                   │   │
                                                    ↓   │                    ↓   │                    ↓   │                   ↓   │
                                                 Secrets │                HubCheck│             Enrollment│            ServiceInst│
                                                        │                        │                       │                      │
                                                    Spinup──> HubSpinup ──Back───┘                       │                      │
                                                                  (or auto-pop on success)               │                      │
```

### Gaps to fix

| Gap | Screen | Fix |
|-----|--------|-----|
| No Back button | SecretsScreen | Add `Back` button that calls `app.pop_screen()` |
| No global quit | PortholeApp | Add `ctrl+q` key binding that calls `app.exit()` with a confirmation |

### Test categories

1. **Forward navigation** — clicking Continue on each screen pushes the correct
   next screen onto the stack.
2. **Back navigation** — clicking Back on every screen (except Prerequisites)
   pops back to the previous screen.
3. **Global quit** — pressing `ctrl+q` from any screen exits the app.
4. **Continue button gating** — the Continue button is disabled when
   preconditions are not met and enabled when they are.
5. **Error state display** — when a worker fails or state is missing, the screen
   shows the correct error message and disables forward navigation.
6. **Screen lifecycle** — `on_mount` fires correctly, workers complete, reactive
   state updates propagate to widgets.

## Acceptance Criteria

### AC-1: Back button on every non-initial screen

**Given** the user is on any screen other than PrerequisitesScreen
**When** they click the Back button
**Then** the app pops back to the previous screen in the stack

Screens that must have Back: Secrets, HubCheck, HubSpinup, Enrollment,
ServiceInstall, Summary. (HubCheck, HubSpinup, Enrollment, ServiceInstall, and
Summary already have it. Secrets does not — must be added.)

### AC-2: Global quit from any screen

**Given** the user is on any screen
**When** they press `ctrl+q`
**Then** the app exits cleanly

### AC-3: Forward navigation with mocked dependencies

**Given** all external dependencies are mocked (tools installed, state valid,
subprocess success)
**When** the user clicks Continue through the entire wizard
**Then** each screen transition pushes the correct screen type
**And** the screen stack depth matches expectations

### AC-4: Continue button disabled when preconditions unmet

| Screen | Disabled when |
|--------|--------------|
| Prerequisites | Any tool not installed |
| Secrets | age_ok, sops_ok, or state_ok is False |
| HubCheck | State error (no Continue shown) |
| Enrollment | Not yet enrolled (no Continue shown until enrollment completes) |
| ServiceInstall | Scripts dir missing (Install button disabled; no Continue until install) |

**Given** the precondition is not met
**When** the screen renders
**Then** the Continue (or action) button is disabled

### AC-5: Error states show correct messages

| Screen | Error condition | Expected behavior |
|--------|----------------|-------------------|
| HubCheck | `load_state` raises `StateNotFoundError` | Shows error, only Back button |
| HubCheck | ping fails | Shows unreachable message, offers Spinup and Skip |
| Enrollment | `load_state` raises | Shows error, only Back button |
| Enrollment | `porthole add` fails (rc != 0) | Shows failure, re-enables Enroll |
| ServiceInstall | scripts dir missing | Install button disabled |
| Summary | checks fail | Banner shows failure count |

### AC-6: Full 3-screen flow test

**Given** mocks for installed tools, valid state, and subprocess success
**When** a single test navigates Prerequisites → Secrets → HubCheck
**Then** screen transitions succeed and widget state is correct at each step

## Scope & Constraints

### In scope
- Pilot-based pytest tests for all 7 screens
- Adding Back button to SecretsScreen
- Adding `ctrl+q` global quit binding to PortholeApp
- Shared test fixtures in `tests/conftest.py` (or `tests/conftest_tui.py`)
- Mock helpers for `asyncio.create_subprocess_exec` and `subprocess.run`

### Out of scope
- tmux/libtmux end-to-end smoke tests (future work, not this spec)
- pytest-textual-snapshot visual regression (can be added later)
- Testing the actual CLI entry point (`porthole-setup`)
- Testing real subprocess execution (always mocked)

### Constraints
- Tests must run headlessly (`run_test(headless=True)`) with no TTY
- Tests must not call real system commands — all subprocess calls mocked
- No new dev dependencies beyond `pytest>=8.0` (already present) and
  `pytest-asyncio` (needed for async tests)

## Implementation Approach

### 1. Add missing navigation (app + SecretsScreen)

- `PortholeApp`: add `BINDINGS = [("ctrl+q", "quit", "Quit")]`
- `SecretsScreen.compose()`: add Back button alongside Continue
- `SecretsScreen`: add `#back-btn` handler calling `app.pop_screen()`

### 2. Create test infrastructure

- Add `pytest-asyncio` to `[dependency-groups] dev`
- Create `tests/conftest_tui.py` with shared fixtures:
  - `mock_all_installed` — patch `is_installed` to return True
  - `mock_network_state` — patch `load_state` to return test NetworkState
  - `mock_subprocess_success` — no-op all subprocess calls
  - `mock_suspend` — `App.suspend()` → `contextlib.nullcontext()`
  - `make_fake_subprocess(rc, stdout_lines)` — configurable async subprocess mock

### 3. Write test modules

| Module | Coverage |
|--------|----------|
| `tests/test_tui_navigation.py` | Forward nav, back nav, global quit, screen stack |
| `tests/test_tui_prerequisites.py` | Tool detection, install flow, Continue gating |
| `tests/test_tui_secrets.py` | Reactive state, button gating, age/sops/state checks |
| `tests/test_tui_hub_check.py` | State errors, ping success/fail, Spinup routing |
| `tests/test_tui_enrollment.py` | Form rendering, enrollment flow, re-sync, already-registered |
| `tests/test_tui_service_install.py` | Install flow, platform branching, verify step |
| `tests/test_tui_summary.py` | Check results, banner state, Finish exits app |

### 4. Mock strategy (from SPIKE-008)

Mock at function boundary, not subprocess level:
- L1: `is_installed`, `detect_os`, `get_install_command`
- L2: `load_state` → fixture NetworkState
- L3: Path constants → `tmp_path`
- L4: `asyncio.create_subprocess_exec` → `make_fake_subprocess`
- L5: `subprocess.run` → MagicMock(returncode=0)
- L6: `App.suspend()` → `nullcontext()`

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-05 | 39958ca | Initial creation |
