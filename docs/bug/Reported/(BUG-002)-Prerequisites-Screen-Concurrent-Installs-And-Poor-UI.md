---
title: "Prerequisites screen: TUI should not be a package manager — delegate to ansible"
artifact: BUG-002
status: Reported
author: cristos
created: 2026-03-06
last-updated: 2026-03-06
severity: high
affected-artifacts: []
discovered-in: "Manual testing of porthole setup TUI — clicked Install All, terraform installed but remaining tools failed silently"
fix-ref: "BUG002-epic"
depends-on: []
execution-tracking: required
---

# Prerequisites screen: TUI should not be a package manager — delegate to ansible

## Description

The prerequisites screen (`src/porthole_setup/screens/prerequisites.py`) has two interrelated defects: a concurrency bug in "Install All" that causes most installs to silently fail, and several UI quality problems that make the screen confusing and unresponsive.

### Concurrency bug

`_install_all()` iterates over all missing tools and calls `self._run_install()` for each one. Because `_run_install` is decorated with `@work(exclusive=False)`, every install launches as a concurrent Textual worker. On Linux, multiple tools (`wireguard-tools`, `age`, `terraform`) use `sudo apt-get install`, which requires an exclusive dpkg lock. When these run simultaneously:

- Terraform (the longest install — adds a GPG key, apt repo, runs `apt-get update`, then installs) tends to acquire the lock first and succeed.
- The other `apt-get` invocations fail with dpkg lock contention errors.
- The user sees terraform complete, then the UI appears to "stop" — no further progress, no error messages surfaced clearly.

### UI quality problems

1. **Full widget teardown on every state change.** `_rebuild_rows()` calls `container.remove_children()` then re-mounts everything. This causes visible flicker and destroys scroll position.
2. **Interleaved log output.** All concurrent installs write to the same `RichLog` widget. Output from different tools mixes together, making it unreadable.
3. **No progress indication.** During "Install All", the user cannot tell which tool is currently installing, which are queued, or which have finished.
4. **No error recovery.** If an install fails mid-batch, there's no way to retry just that tool without re-running the whole flow. The failed state isn't clearly surfaced.
5. **Hidden log panel.** The `RichLog` has `display: none` by default and only appears when an install starts. Before that, users see no feedback area at all.

## Reproduction Steps

1. Run the porthole setup TUI on a Linux machine where most tools are missing.
2. Click "Install All Missing".
3. Observe terraform installs successfully.
4. Observe the UI appears to stop — no further installs proceed, and any apt-based tools that ran concurrently likely failed due to dpkg lock contention.
5. No clear error messages are shown for the failed installs.

## Expected Behavior

- `setup.sh` bootstraps uv + ansible as the only shell-level prereqs.
- The TUI runs an ansible playbook to install all remaining tools.
- Ansible output streams to the screen in real time.
- On success, the Continue button enables.
- On failure, the user sees ansible's error output and can retry.

## Actual Behavior

- All installs fire concurrently, causing dpkg lock conflicts on Linux.
- Terraform succeeds; other apt-based tools fail silently.
- The UI appears to freeze after terraform completes.
- Log output from concurrent installs is interleaved and unreadable.
- The full widget list flickers on every state change.
- No retry mechanism for individual failed installs.

## Impact

This is the first screen users see in the setup wizard. When it fails silently after one tool installs, users have no way to proceed and no clear indication of what went wrong. The poor UI quality compounds the problem — even when installs work individually, the experience feels broken.

## Fix approach

**The previous fix (concurrent-to-sequential refactor, commit 6f817e2) was wrong.** It improved the mechanics but preserved the flawed architecture: the TUI acting as a package manager. The TUI should not install tools at all — that's what ansible is for.

### Root cause

The real problem isn't concurrency vs sequencing — it's that the TUI reimplements package management poorly (custom install commands per tool per OS, sudo prompting, PATH manipulation, error recovery). Ansible already solves all of this with idempotent, declarative, cross-platform package installation.

### Correct approach: delegate to ansible

**Bootstrap chain:**
1. `setup.sh` ensures only two prerequisites: **uv** and **ansible** (via `uv tool install ansible`)
2. A new `ansible/prereqs.yml` playbook declares the remaining tools as ansible tasks
3. The prerequisites screen simply runs `ansible-playbook ansible/prereqs.yml`, streams output, and shows pass/fail

**What this eliminates:**
- `platform.py`'s `INSTALL_COMMANDS` dict and all per-tool install logic
- `NEEDS_SUDO` set and sudo warning UI
- The entire install queue, ToolStatus enum, per-tool buttons, spinner, timer
- Interactive password prompting from the TUI
- Manual PATH manipulation and binary-not-found workarounds

**What the screen becomes:**
- On mount: run `ansible-playbook ansible/prereqs.yml` in a background thread
- Stream ansible output to a RichLog (full screen, no sidebar needed)
- On success: enable Continue button
- On failure: show error summary, offer Retry button
- That's it — ~100 lines instead of ~350

### Implementation tasks

1. **Update `setup.sh`** — add ansible bootstrapping (`uv tool install ansible` if `ansible-playbook` not on PATH)
2. **Create `ansible/prereqs.yml`** — local playbook that installs wireguard-tools, sops, age, terraform, porthole (via uv). Use `become: yes` for system packages. Handle both Linux (apt) and macOS (homebrew) via ansible's built-in modules.
3. **Rewrite `prerequisites.py`** — strip down to: run ansible-playbook, stream output, show pass/fail, retry on failure. Use `@work(thread=True)` + `subprocess.Popen` + `call_from_thread` pattern from workstation.
4. **Simplify `platform.py`** — remove `INSTALL_COMMANDS`, `NEEDS_SUDO`, `get_install_command()`, `get_manual_hint()`, `MANUAL_INSTALL_HINTS`. Keep only `detect_os()`, `is_installed()`, `TOOL_DESCRIPTIONS`, `get_tool_description()` (still useful for display).
5. **Update tests** — adapt `test_tui_prerequisites.py` and `conftest_tui.py` to the new screen structure.

### Affected files

- `setup.sh` — add ansible bootstrapping
- `ansible/prereqs.yml` — **new** — local prerequisites playbook
- `src/porthole_setup/screens/prerequisites.py` — rewrite to ansible runner
- `src/porthole_setup/platform.py` — remove install command infrastructure
- `tests/test_tui_prerequisites.py` — adapt to new screen
- `tests/conftest_tui.py` — update mocks

### Reference patterns

- `~/Documents/202602-workstation/scripts/setup_tui/lib/prereqs.py` — prereqs installer that bootstraps ansible via uv
- `~/Documents/202602-workstation/scripts/setup_tui/screens/bootstrap.py` — `_run_streaming` for subprocess output, `_step_ansible` for playbook invocation
- `~/Documents/202602-workstation/setup.sh` — two-stage bootstrap (bash shim → TUI)

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Reported | 2026-03-06 | — | Initial report |
