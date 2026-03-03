"""Entry point for porthole_setup TUI."""

from __future__ import annotations

import sys


def _run_check() -> None:
    """Non-interactive mode: print status and exit 0/1.

    Full implementation pending Summary screen (task iac-remote-desktop-node-690).
    For now, run the prerequisite and secret checks and report results.
    """
    from porthole_setup.platform import is_installed  # noqa: PLC0415
    from porthole_setup.screens.prerequisites import TOOLS  # noqa: PLC0415
    from porthole_setup.screens.secrets import (  # noqa: PLC0415
        AGE_KEY_PATH,
        SOPS_CONFIG_PATH,
        STATE_PATH,
        _summarise_state,
    )

    results: list[tuple[str, bool, str]] = []

    for binary, display, _ in TOOLS:
        ok = is_installed(binary)
        results.append((f"tool:{display}", ok, "installed" if ok else "missing"))

    results.append(("age-key", AGE_KEY_PATH.exists(), str(AGE_KEY_PATH)))
    results.append((".sops.yaml", SOPS_CONFIG_PATH.exists(), str(SOPS_CONFIG_PATH)))

    state_ok = STATE_PATH.exists()
    state_detail = _summarise_state() if state_ok else "missing"
    results.append(("network.sops.yaml", state_ok, state_detail or "decrypt failed"))

    all_ok = all(ok for _, ok, _ in results)
    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        icon = "✓" if ok else "✗"
        print(f"  {icon}  {name:<{width}}  {detail}")

    if all_ok:
        print("\nAll checks passed.")
        sys.exit(0)
    else:
        failed = sum(1 for _, ok, _ in results if not ok)
        print(f"\n{failed} check(s) failed.")
        sys.exit(1)


def main() -> None:
    """Parse flags and launch the Textual app (or run --check mode)."""
    args = sys.argv[1:]

    if "--check" in args:
        _run_check()
        return

    from porthole_setup.app import PortholeApp  # noqa: PLC0415
    app = PortholeApp()
    app.run()


if __name__ == "__main__":
    main()
