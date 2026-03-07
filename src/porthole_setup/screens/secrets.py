"""Secrets screen — manage age key and .sops.yaml configuration."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RichLog

_log = logging.getLogger(__name__)

AGE_KEY_PATH = Path.home() / ".config" / "sops" / "age" / "keys.txt"
SOPS_CONFIG_PATH = Path(".sops.yaml")

CSS = """
SecretsScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.status-ok  { color: $success; margin: 0 1; }
.status-bad { color: $error;   margin: 0 1; }
.info { color: $text-muted; margin: 0 1 1 1; }
.action-row { layout: horizontal; height: 3; margin: 0 1; }
#log { height: 10; border: solid $primary; margin: 1; display: none; }
#log.visible { display: block; }
#continue-btn { margin: 1; dock: bottom; }
"""


def _age_pubkey_from_keyfile(path: Path) -> str | None:
    """Extract the age public key from the keys.txt file."""
    try:
        text = path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# public key:"):
                return line.split(":", 1)[1].strip()
        return None
    except OSError:
        return None


class SecretsScreen(Screen):
    """Manage age key and .sops.yaml configuration."""

    TITLE = "Step 2 of 5: Secrets"
    CSS = CSS

    age_ok: reactive[bool] = reactive(False)
    sops_ok: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.age_ok = AGE_KEY_PATH.exists()
        self.sops_ok = SOPS_CONFIG_PATH.exists()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            # --- Age key ---
            Label("Age encryption key", classes="section-title"),
            Label(
                ("✓ Key found" if self.age_ok else "✗ Key not found"),
                id="age-status",
                classes="status-ok" if self.age_ok else "status-bad",
            ),
            Label(str(AGE_KEY_PATH), classes="info"),
            Vertical(
                Button(
                    "Generate key" if not self.age_ok else "Regenerate key (will break existing state)",
                    id="age-btn",
                    variant="primary" if not self.age_ok else "warning",
                ),
                id="age-action",
                classes="action-row",
            ),
            # --- .sops.yaml ---
            Label(".sops.yaml configuration", classes="section-title"),
            Label(
                ("✓ Found" if self.sops_ok else "✗ Not found"),
                id="sops-status",
                classes="status-ok" if self.sops_ok else "status-bad",
            ),
            Vertical(
                Button(
                    "Write from age key" if not self.sops_ok else "Overwrite from age key",
                    id="sops-btn",
                    variant="primary" if not self.sops_ok else "warning",
                    disabled=not self.age_ok,
                ),
                id="sops-action",
                classes="action-row",
            ),
            RichLog(id="log", highlight=True, markup=True),
        )
        all_ok = self.age_ok and self.sops_ok
        yield Button("Continue →", id="continue-btn", variant="success", disabled=not all_ok)
        yield Button("← Back", id="back-btn", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_ui()

    # ------------------------------------------------------------------
    # Reactive watches
    # ------------------------------------------------------------------

    def watch_age_ok(self, ok: bool) -> None:
        try:
            self.query_one("#age-status", Label).update("✓ Key found" if ok else "✗ Key not found")
            self.query_one("#age-status").set_class(ok, "status-ok")
            self.query_one("#age-status").set_class(not ok, "status-bad")
        except Exception:  # noqa: BLE001
            pass
        self._refresh_ui()

    def watch_sops_ok(self, ok: bool) -> None:
        try:
            self.query_one("#sops-status", Label).update("✓ Found" if ok else "✗ Not found")
            self.query_one("#sops-status").set_class(ok, "status-ok")
            self.query_one("#sops-status").set_class(not ok, "status-bad")
        except Exception:  # noqa: BLE001
            pass
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        try:
            self.query_one("#sops-btn", Button).disabled = not self.age_ok
            self.query_one("#continue-btn", Button).disabled = not (self.age_ok and self.sops_ok)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#age-btn")
    def _age_pressed(self) -> None:
        if self.age_ok:
            self._show_log()
            self._log_markup("[bold yellow]Warning: regenerating the age key will break decryption of existing network.sops.yaml.[/]")
            self._log_markup("If you proceed, you will need to re-initialize the network state.")
            btn = self.query_one("#age-btn", Button)
            btn.label = "Yes, regenerate key (I understand)"
            btn.variant = "error"
            btn.id = "age-confirm-btn"
        else:
            self._generate_age_key()

    @on(Button.Pressed, "#age-confirm-btn")
    def _age_confirm(self) -> None:
        self._generate_age_key()

    @work(thread=True, exclusive=True)
    def _generate_age_key(self) -> None:
        self.app.call_from_thread(self._show_log)
        self.app.call_from_thread(self._log_markup, "[bold]Generating age key…[/]")

        AGE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["age-keygen", "-o", str(AGE_KEY_PATH)],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            for line in result.stdout.splitlines():
                self.app.call_from_thread(self._log_markup, line)
        if result.stderr:
            for line in result.stderr.splitlines():
                self.app.call_from_thread(self._log_markup, line)

        if result.returncode == 0:
            self.app.call_from_thread(self._log_markup, "[bold green]✓ Age key generated[/]")
            self.age_ok = True
            pubkey = _age_pubkey_from_keyfile(AGE_KEY_PATH)
            if pubkey:
                self.app.call_from_thread(self._log_markup, f"Public key: [bold]{pubkey}[/]")

            def _reset_btn() -> None:
                btn = self.query_one("[id^='age']", Button)
                btn.label = "Regenerate key (will break existing state)"
                btn.variant = "warning"
                btn.id = "age-btn"

            self.app.call_from_thread(_reset_btn)
        else:
            self.app.call_from_thread(
                self._log_markup,
                f"[bold red]✗ age-keygen failed (exit {result.returncode})[/]",
            )

    @on(Button.Pressed, "#sops-btn")
    def _sops_pressed(self) -> None:
        self._write_sops_config()

    @work(thread=True, exclusive=True)
    def _write_sops_config(self) -> None:
        self.app.call_from_thread(self._show_log)
        pubkey = _age_pubkey_from_keyfile(AGE_KEY_PATH)
        if not pubkey:
            self.app.call_from_thread(
                self._log_markup, "[bold red]✗ Could not read age public key from key file[/]"
            )
            return
        content = _SOPS_YAML_TEMPLATE.format(age_pubkey=pubkey)
        SOPS_CONFIG_PATH.write_text(content)
        self.app.call_from_thread(
            self._log_markup, f"[bold green]✓ .sops.yaml written (public key: {pubkey})[/]"
        )
        self.sops_ok = True

    @on(Button.Pressed, "#back-btn")
    def _back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.hub_check import HubCheckScreen  # noqa: PLC0415
        self.app.push_screen(HubCheckScreen())

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _show_log(self) -> None:
        self.query_one("#log", RichLog).add_class("visible")

    def _log_markup(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)


_SOPS_YAML_TEMPLATE = """\
creation_rules:
  - path_regex: network\\.sops\\.yaml$
    encrypted_regex: "^private_key$"
    age: "{age_pubkey}"
"""
