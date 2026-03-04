"""Service installation screen — install service files and bring WireGuard up."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

from porthole_setup.platform import OS, detect_os

CSS = """
ServiceInstallScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.info    { color: $text-muted; margin: 0 1; }
.warning { color: $warning;   margin: 0 1; }
#log { height: 22; border: solid $primary; margin: 1; }
#button-row { layout: horizontal; height: 3; margin: 1; }
"""

_USRLOCAL_BIN  = Path("/usr/local/bin")
_SYSTEMD_DIR   = Path("/etc/systemd/system")
_WIREGUARD_DIR = Path("/etc/wireguard")
_LAUNCHDAEMON  = Path("/Library/LaunchDaemons")


class ServiceInstallScreen(Screen):
    """Copy service files to system paths and start WireGuard on this node."""

    TITLE = "Step 4b: Service Installation"
    CSS = CSS

    def __init__(self, peer_name: str) -> None:
        super().__init__()
        self._peer_name = peer_name
        self._os = detect_os()
        self._running = False
        self._scripts_dir = Path(f"peer-scripts/{peer_name}")

    def compose(self) -> ComposeResult:
        os_label = "Linux" if self._os == OS.LINUX else "macOS"
        scripts_ok = self._scripts_dir.exists()
        yield Header()
        yield ScrollableContainer(
            Label("Service installation", classes="section-title"),
            Static(
                f"Platform: [bold]{os_label}[/]   "
                f"Peer: [bold]{self._peer_name}[/]   "
                f"Scripts: {'[green]✓[/]' if scripts_ok else '[red]✗ missing — run enrollment first[/]'} "
                f"({self._scripts_dir}/)",
                markup=True,
                classes="info",
            ),
            Label("sudo required", classes="section-title"),
            Static(
                "Service files are copied to system paths and services are enabled. "
                "You will be prompted for your password if passwordless sudo is not configured.",
                classes="warning",
            ),
            Label("What will be installed", classes="section-title"),
            Static(
                self._install_summary(),
                markup=True,
                classes="info",
            ),
            RichLog(id="log", highlight=True, markup=True),
            Vertical(id="button-row"),
        )
        yield Footer()

    def on_mount(self) -> None:
        row = self.query_one("#button-row", Vertical)
        scripts_ok = self._scripts_dir.exists()
        row.mount(
            Button(
                "Install & Start Services",
                id="install-btn",
                variant="primary",
                disabled=not scripts_ok,
            ),
            Button("← Back", id="back-btn", variant="default"),
        )

    def _install_summary(self) -> str:
        name = self._peer_name
        if self._os == OS.LINUX:
            return (
                f"  [dim]•[/] wg-watchdog.sh, wg-status-server.py → /usr/local/bin/\n"
                f"  [dim]•[/] wg-watchdog.service, wg-watchdog.timer → /etc/systemd/system/\n"
                f"  [dim]•[/] ssh-tunnel-{name}.service, wg-status-server.service → /etc/systemd/system/\n"
                f"  [dim]•[/] wg0.conf → /etc/wireguard/wg0.conf\n"
                f"  [dim]•[/] systemctl enable --now wg-quick@wg0 wg-watchdog.timer ..."
            )
        return (
            f"  [dim]•[/] wg-watchdog.sh, wg-status-server.py → /usr/local/bin/\n"
            f"  [dim]•[/] wg-watchdog.plist, ssh-tunnel-{name}.plist, wg-status-server.plist → /Library/LaunchDaemons/\n"
            f"  [dim]•[/] wg0.conf → /etc/wireguard/wg0.conf\n"
            f"  [dim]•[/] launchctl load -w for each plist"
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#back-btn")
    def _back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#install-btn")
    def _install(self) -> None:
        if self._running:
            return
        self._running = True
        self.query_one("#install-btn", Button).disabled = True
        if self._os == OS.LINUX:
            self._run_linux_install()
        else:
            self._run_macos_install()

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        try:
            from porthole_setup.screens.summary import SummaryScreen  # noqa: PLC0415
            self.app.push_screen(SummaryScreen(peer_name=self._peer_name))
        except ImportError:
            # Summary screen not yet implemented — exit cleanly
            self.app.exit(message="Setup complete! Node enrolled and services active.")

    # ------------------------------------------------------------------
    # Linux install worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_linux_install(self) -> None:
        log = self.query_one("#log", RichLog)
        d = self._scripts_dir
        name = self._peer_name
        tunnel_unit = f"ssh-tunnel-{name}.service"

        steps: list[tuple[str, list[str]]] = [
            (
                "Copy scripts",
                [
                    "sudo", "cp",
                    str(d / "wg-watchdog.sh"),
                    str(d / "wg-status-server.py"),
                    str(_USRLOCAL_BIN) + "/",
                ],
            ),
            (
                "Make scripts executable",
                [
                    "sudo", "chmod", "+x",
                    str(_USRLOCAL_BIN / "wg-watchdog.sh"),
                    str(_USRLOCAL_BIN / "wg-status-server.py"),
                ],
            ),
            (
                "Copy systemd units",
                [
                    "sudo", "cp",
                    str(d / "wg-watchdog.service"),
                    str(d / "wg-watchdog.timer"),
                    str(d / "wg-status-server.service"),
                    str(d / tunnel_unit),
                    str(_SYSTEMD_DIR) + "/",
                ],
            ),
            (
                "Install WireGuard config",
                [
                    "sudo", "install", "-m", "600",
                    str(d / "wg0.conf"),
                    str(_WIREGUARD_DIR / "wg0.conf"),
                ],
            ),
            ("Reload systemd", ["sudo", "systemctl", "daemon-reload"]),
            (
                "Enable and start services",
                [
                    "sudo", "systemctl", "enable", "--now",
                    "wg-quick@wg0",
                    "wg-watchdog.timer",
                    tunnel_unit,
                    "wg-status-server.service",
                ],
            ),
        ]

        for desc, cmd in steps:
            log.write(f"\n[bold]$ {' '.join(cmd)}[/]  [dim]# {desc}[/]")
            rc = await self._stream(log, cmd)
            if rc != 0:
                self._finish_failed(log, f"Failed: {desc} (exit {rc})")
                return

        await self._verify_and_finish(log)

    # ------------------------------------------------------------------
    # macOS install worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_macos_install(self) -> None:
        log = self.query_one("#log", RichLog)
        d = self._scripts_dir
        name = self._peer_name

        # Copy scripts
        for desc, cmd in [
            (
                "Copy scripts",
                [
                    "sudo", "cp",
                    str(d / "wg-watchdog.sh"),
                    str(d / "wg-status-server.py"),
                    str(_USRLOCAL_BIN) + "/",
                ],
            ),
            (
                "Make scripts executable",
                [
                    "sudo", "chmod", "+x",
                    str(_USRLOCAL_BIN / "wg-watchdog.sh"),
                    str(_USRLOCAL_BIN / "wg-status-server.py"),
                ],
            ),
            (
                "Install WireGuard config",
                [
                    "sudo", "install", "-m", "600",
                    str(d / "wg0.conf"),
                    str(_WIREGUARD_DIR / "wg0.conf"),
                ],
            ),
        ]:
            log.write(f"\n[bold]$ {' '.join(cmd)}[/]  [dim]# {desc}[/]")
            rc = await self._stream(log, cmd)
            if rc != 0:
                self._finish_failed(log, f"Failed: {desc} (exit {rc})")
                return

        # Copy and load each plist
        plists = [
            d / "wg-watchdog.plist",
            d / f"ssh-tunnel-{name}.plist",
            d / "wg-status-server.plist",
        ]
        for plist_path in plists:
            if not plist_path.exists():
                log.write(f"[dim]  skipping {plist_path.name} (not found in scripts dir)[/]")
                continue
            dest = _LAUNCHDAEMON / plist_path.name
            copy_cmd = ["sudo", "cp", str(plist_path), str(dest)]
            log.write(f"\n[bold]$ {' '.join(copy_cmd)}[/]")
            if await self._stream(log, copy_cmd) != 0:
                self._finish_failed(log, f"Failed to copy {plist_path.name}")
                return
            load_cmd = ["sudo", "launchctl", "load", "-w", str(dest)]
            log.write(f"[bold]$ {' '.join(load_cmd)}[/]")
            rc = await self._stream(log, load_cmd)
            if rc != 0:
                log.write(
                    f"[yellow]  Warning: launchctl load returned {rc} for {plist_path.name}[/]"
                )

        await self._verify_and_finish(log)

    # ------------------------------------------------------------------
    # Shared post-install verification
    # ------------------------------------------------------------------

    async def _verify_and_finish(self, log: RichLog) -> None:
        log.write("\n[bold]Bringing up WireGuard interface…[/]")
        rc = await self._stream(log, ["sudo", "wg-quick", "up", "wg0"])
        if rc != 0:
            log.write("[yellow]  wg-quick up returned non-zero (interface may already be active)[/]")

        # Check wg show
        log.write("\n[bold]$ wg show wg0[/]")
        try:
            proc = await asyncio.create_subprocess_exec(
                "wg", "show", "wg0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            wg_up = proc.returncode == 0 and bool(stdout.strip())
            if wg_up:
                log.write("[bold green]✓ WireGuard interface wg0 is up[/]")
            else:
                log.write("[bold red]✗ wg0 not active — WireGuard may still be initialising[/]")
        except Exception as exc:  # noqa: BLE001
            log.write(f"[yellow]  wg show: {exc}[/]")

        # Ping hub
        hub_host = self._get_hub_host()
        if hub_host:
            log.write(f"\n[bold]Pinging hub {hub_host}…[/]")
            try:
                proc2 = await asyncio.create_subprocess_exec(
                    "ping", "-c", "1", "-W", "3", hub_host,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                rc2 = await asyncio.wait_for(proc2.wait(), timeout=6)
                icon = "[green]✓[/]" if rc2 == 0 else "[red]✗[/]"
                log.write(
                    f"{icon} Hub ping {'succeeded' if rc2 == 0 else 'failed'} "
                    f"(hub: {hub_host})"
                )
            except Exception as exc:  # noqa: BLE001
                log.write(f"[yellow]  Ping failed: {exc}[/]")
        else:
            log.write("[dim]  Skipping hub ping (could not load state)[/]")

        log.write("\n[bold green]✓ Service installation complete[/]")
        self._running = False
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(
            Button("Continue →", id="continue-btn", variant="success"),
            Button("← Back", id="back-btn", variant="default"),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _stream(self, log: RichLog, cmd: list[str]) -> int:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None
            async for raw in proc.stdout:
                log.write(raw.decode(errors="replace").rstrip())
            return await proc.wait()
        except FileNotFoundError as exc:
            log.write(f"[bold red]✗ Command not found: {exc}[/]")
            return 1
        except Exception as exc:  # noqa: BLE001
            log.write(f"[bold red]✗ Unexpected error: {exc}[/]")
            return 1

    def _finish_failed(self, log: RichLog, msg: str) -> None:
        log.write(f"\n[bold red]✗ {msg}[/]")
        self._running = False
        try:
            self.query_one("#install-btn", Button).disabled = False
        except Exception:  # noqa: BLE001
            pass

    def _get_hub_host(self) -> str | None:
        try:
            from porthole_setup.state import load_state  # noqa: PLC0415
            state = load_state()
            return state.endpoint.split(":")[0] if state.endpoint else None
        except Exception:  # noqa: BLE001
            return None
