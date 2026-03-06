"""Entry point for porthole_setup TUI."""

from __future__ import annotations

import sys


def _run_check() -> None:
    """Non-interactive mode: run all setup checks, print status, exit 0/1."""
    import socket  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    from porthole_setup.platform import is_installed  # noqa: PLC0415
    from porthole_setup.screens.prerequisites import TOOLS  # noqa: PLC0415
    from porthole_setup.screens.secrets import (  # noqa: PLC0415
        AGE_KEY_PATH,
        SOPS_CONFIG_PATH,
        STATE_PATH,
        _summarise_state,
    )
    from porthole_setup.state import load_state  # noqa: PLC0415

    results: list[tuple[str, bool, str]] = []

    # --- Prerequisites ---
    for binary, display, _ in TOOLS:
        ok = is_installed(binary)
        results.append((f"tool:{display}", ok, "installed" if ok else "missing"))

    # --- Secrets ---
    results.append(("age-key", AGE_KEY_PATH.exists(), str(AGE_KEY_PATH)))
    results.append((".sops.yaml", SOPS_CONFIG_PATH.exists(), str(SOPS_CONFIG_PATH)))

    state_ok = STATE_PATH.exists()
    state_detail = _summarise_state() if state_ok else "missing"
    results.append(("network.sops.yaml", state_ok, state_detail or "decrypt failed"))

    # --- Hub reachability ---
    hub_host: str | None = None
    try:
        state = load_state()
        hub_host = state.endpoint.split(":")[0] if state.endpoint else None
    except Exception:  # noqa: BLE001
        pass

    if hub_host:
        try:
            rc = subprocess.run(
                ["ping", "-c", "1", "-W", "3", hub_host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=6,
            ).returncode
            hub_ok = rc == 0
        except Exception:  # noqa: BLE001
            hub_ok = False
        results.append(("hub:reachable", hub_ok, hub_host if hub_ok else f"unreachable ({hub_host})"))
    else:
        results.append(("hub:reachable", False, "hub host unknown (state unavailable)"))

    # --- Enrollment ---
    hostname = socket.gethostname()
    try:
        state = load_state()
        peer = state.get_peer(hostname)
        enroll_ok = peer is not None
        enroll_detail = f"{hostname} → {peer.ip}" if peer else f"'{hostname}' not in state"
    except Exception:  # noqa: BLE001
        enroll_ok = False
        enroll_detail = "could not load state"
    results.append(("node:enrolled", enroll_ok, enroll_detail))

    # --- WireGuard ---
    try:
        proc = subprocess.run(
            ["wg", "show", "wg0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        wg_ok = proc.returncode == 0 and bool(proc.stdout.strip())
        wg_detail = "wg0 active" if wg_ok else "wg0 not active"
    except FileNotFoundError:
        wg_ok = False
        wg_detail = "wireguard-tools not installed"
    except Exception:  # noqa: BLE001
        wg_ok = False
        wg_detail = "check failed"
    results.append(("wireguard:wg0", wg_ok, wg_detail))

    # --- Report ---
    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        icon = "✓" if ok else "✗"
        print(f"  {icon}  {name:<{width}}  {detail}")

    all_ok = all(ok for _, ok, _ in results)
    if all_ok:
        print("\nAll checks passed.")
        sys.exit(0)
    else:
        failed = sum(1 for _, ok, _ in results if not ok)
        print(f"\n{failed} check(s) failed.")
        sys.exit(1)


def main() -> None:
    """Parse flags and launch the Textual app (or run --check mode)."""
    import logging  # noqa: PLC0415

    args = sys.argv[1:]

    if "--check" in args:
        _run_check()
        return

    debug = "--debug" in args

    # Set up file logging so crashes are captured even when the TUI
    # takes over the terminal.
    log_path = _setup_logging(debug)
    log = logging.getLogger("porthole_setup")
    log.info("porthole-setup starting (Python %s)", sys.version)
    log.info("args=%s, debug=%s", args, debug)

    # Validate imports before handing off to Textual
    try:
        log.info("Importing modules…")
        from porthole_setup.app import PortholeApp  # noqa: PLC0415
        from porthole_setup.platform import (  # noqa: PLC0415
            INSTALL_COMMANDS,
            NEEDS_SUDO,
            TOOL_DESCRIPTIONS,
            detect_os,
        )
        from porthole_setup.screens.prerequisites import TOOLS  # noqa: PLC0415

        os_type = detect_os()
        log.info("OS detected: %s", os_type)
        log.info("Tools to check: %s", [t[1] for t in TOOLS])
        log.info("Install commands available for: %s", list(INSTALL_COMMANDS.keys()))
        log.info("NEEDS_SUDO: %s", NEEDS_SUDO)
        log.info("Descriptions defined for: %s", list(TOOL_DESCRIPTIONS.keys()))

        import textual  # noqa: PLC0415
        log.info("Textual version: %s", textual.__version__)

    except Exception:
        import traceback  # noqa: PLC0415
        msg = traceback.format_exc()
        log.error("Import failed:\n%s", msg)
        print(f"\nporthole-setup failed to import required modules:\n\n{msg}", file=sys.stderr)
        print(f"Full log at: {log_path}", file=sys.stderr)
        sys.exit(1)

    # Run the TUI
    try:
        log.info("Launching TUI…")
        app = PortholeApp()
        app.run()
        log.info("TUI exited normally")
    except Exception:
        import traceback  # noqa: PLC0415
        msg = traceback.format_exc()
        log.error("TUI crashed:\n%s", msg)
        print(f"\nporthole-setup crashed. Traceback:\n\n{msg}", file=sys.stderr)
        print(f"Full log at: {log_path}", file=sys.stderr)
        sys.exit(1)


def _setup_logging(debug: bool = False) -> str:
    """Configure logging to file; return the log file path."""
    import logging  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    log_dir = Path.home() / ".local" / "state" / "porthole"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "setup.log"

    logging.basicConfig(
        filename=str(log_path),
        filemode="w",
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return str(log_path)


if __name__ == "__main__":
    main()
