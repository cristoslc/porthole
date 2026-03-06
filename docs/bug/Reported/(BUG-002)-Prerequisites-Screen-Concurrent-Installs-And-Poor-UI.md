---
title: "Prerequisites screen: concurrent installs cause failures and UI is poor quality"
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

# Prerequisites screen: concurrent installs cause failures and UI is poor quality

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

- "Install All" should install tools sequentially (queue-based), avoiding dpkg lock contention.
- Each tool should show its own status inline (queued / installing / done / failed) without full widget rebuilds.
- Install output should be clearly delimited per tool.
- Failures should be reported clearly, and the queue should continue to the next tool.
- Failed tools should offer a "Retry" button.
- The log panel (or equivalent feedback area) should be visible by default.

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

Adopt proven patterns from the `202602-workstation` TUI codebase (`~/Documents/202602-workstation/scripts/setup_tui/`), which solves all of these problems in a production-tested way.

### 1. Sequential step pipeline (replaces concurrent workers)

Replace `@work(exclusive=False)` with a single `@work(thread=True)` method that iterates tools sequentially, matching the workstation's bootstrap pattern:

```python
@work(thread=True)
def _install_all_sequential(self) -> None:
    for i, ts in enumerate(queue):
        self.app.call_from_thread(self._update_status, ts, "installing")
        try:
            result = self._run_install_blocking(ts)
        except Exception as exc:
            self.app.call_from_thread(self._update_status, ts, "failed")
            continue
        self.app.call_from_thread(self._update_status, ts, "done" if result else "failed")
```

Reference: `workstation/screens/bootstrap.py` step pipeline pattern (lines ~1127-1140).

### 2. In-place widget updates (replaces teardown/rebuild)

Eliminate `_rebuild_rows()` entirely. Pre-compose all tool rows at mount time. Update state by calling `.update()` on existing Static/Label widgets and toggling `.disabled` on Buttons — never `remove_children()` + re-mount.

Reference: workstation never recreates widgets — uses `query_one("#id", Static).update(new_content)` and `button.disabled = True/False`.

### 3. Step sidebar with progress indication

Add a sidebar or inline status column showing per-tool state with visual indicators:

- `✓` green = installed
- `●` yellow + spinner = installing (spinner frames: `"⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"`)
- `✗` red = failed
- `○` dim = queued/pending

Optional: elapsed timer via `set_interval(1, _tick_elapsed)`.

Reference: workstation's `_update_sidebar(steps, current_idx)` pattern.

### 4. Streaming subprocess via thread + call_from_thread

Replace `asyncio.create_subprocess_exec` with `subprocess.Popen` in a thread worker, streaming stdout line-by-line and posting to the TUI via `call_from_thread`. This matches workstation's `_run_streaming` pattern and is simpler than async subprocess for Textual.

Consider extracting a `ToolRunner` class (like workstation's `lib/runner.py`) that wraps subprocess calls, handles `FileNotFoundError`/`PermissionError` gracefully, and returns structured results.

### 5. Error recovery with retry

On failure: mark tool as `failed` state, log error clearly, continue queue to next tool. After queue completes, show per-tool "Retry" buttons only for failed tools (like workstation's "Retry Failed" pattern that re-runs only failed phases).

Add a `failed` state to the `_TS` dataclass alongside `installed`/`installing`.

### 6. Always-visible log panel

Show the RichLog by default (remove `display: none` from CSS). Pre-create it in `compose()` with a placeholder message. Use `.display` property toggling if needed, not CSS class manipulation.

### Affected files

- `src/porthole_setup/screens/prerequisites.py` — primary fix target (rewrite install logic, widget management, progress tracking)
- `src/porthole_setup/platform.py` — may need minor changes for structured result types

### Reference files (workstation patterns to adapt)

- `~/Documents/202602-workstation/scripts/setup_tui/screens/bootstrap.py` — step pipeline, sidebar, streaming, retry
- `~/Documents/202602-workstation/scripts/setup_tui/lib/runner.py` — ToolRunner subprocess wrapper
- `~/Documents/202602-workstation/scripts/setup_tui/lib/setup_logging.py` — dual-stream logging
- `~/Documents/202602-workstation/scripts/setup_tui/app.py` — CSS patterns, widget update style

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Reported | 2026-03-06 | — | Initial report |
