---
title: "Secrets screen: porthole init fails — no interactive stdin in async worker"
artifact: BUG-003
status: Reported
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
severity: high
affected-artifacts: []
discovered-in: "Manual testing of porthole setup TUI — clicked Initialize State on secrets screen"
fix-ref: ""
depends-on: []
execution-tracking: required
---

# Secrets screen: porthole init fails — no interactive stdin in async worker

## Description

The Secrets screen's "Initialize state" button runs `porthole init` which requires interactive stdin (prompts for hub endpoint). The code at `secrets.py:322-344` uses `self.app.suspend()` inside an `@work(exclusive=True)` async worker to yield the terminal. However, `suspend()` from an async worker context doesn't properly yield the terminal — `porthole init` runs but can't receive user input, so it either fails silently or hangs, and `network.sops.yaml` is never created.

### Root cause

`_init_state` is an `async def` decorated with `@work(exclusive=True)`. Textual runs async workers in the event loop, not a background thread. `self.app.suspend()` needs to be called from either the main thread or a `@work(thread=True)` worker to properly hand the terminal back to the subprocess.

The workstation repo's pattern for interactive operations uses `@work(thread=True)` with `self.app.call_from_thread()` to invoke `suspend()` on the main thread, then blocks the worker thread with a `threading.Event` until the interactive operation completes.

## Reproduction Steps

1. Run `./setup.sh`, pass through prerequisites screen.
2. On Secrets screen, generate age key and write .sops.yaml (these work fine — non-interactive).
3. Click "Initialize state".
4. Observe: the log shows "Initializing network state via porthole init..." and "You will be prompted for the hub endpoint" but no prompt appears.
5. The TUI reappears immediately with "network.sops.yaml not found after porthole init".

## Expected Behavior

- TUI suspends, terminal shows `porthole init` prompts.
- User enters hub endpoint interactively.
- After `porthole init` completes, TUI resumes and detects the new network.sops.yaml.

## Actual Behavior

- `porthole init` runs without interactive stdin.
- No terminal prompt appears — the TUI flashes or resumes immediately.
- network.sops.yaml is not created.
- Error shown twice (user clicked button twice).

## Impact

Blocks the entire setup flow — users cannot proceed past Step 2 without a working network.sops.yaml. This is a critical-path blocker.

## Fix approach

Change `_init_state` from `@work(exclusive=True)` async to `@work(thread=True)` with proper suspend handling:

```python
@work(thread=True, exclusive=True)
def _init_state(self) -> None:
    self.app.call_from_thread(self._log_markup, "Initializing...")

    def _do_init():
        with self.app.suspend():
            subprocess.run(["porthole", "init"], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    self.app.call_from_thread(_do_init)
    # ... check result
```

Alternatively, the same pattern should be applied to `_generate_age_key` and `_write_sops_config` for consistency — convert all workers from async to thread-based.

### Affected files

- `src/porthole_setup/screens/secrets.py` — fix worker type and suspend pattern

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Reported | 2026-03-07 | — | Initial report |
