"""Hub spinup screen — run terraform apply + ansible-playbook with live output."""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static

# Map provider slug → terraform directory
PROVIDER_DIRS: dict[str, Path] = {
    "hetzner":      Path("terraform-hetzner"),
    "digitalocean": Path("terraform"),
}
ANSIBLE_DIR = Path("ansible")

# (value, display label) pairs for the provider Select widgets
PROVIDER_OPTIONS = [
    ("hetzner",      "Hetzner Cloud"),
    ("digitalocean", "DigitalOcean"),
]

DNS_PROVIDER_OPTIONS = [
    ("none",         "None (manual)"),
    ("cloudflare",   "Cloudflare"),
    ("digitalocean", "DigitalOcean"),
    ("hetzner",      "Hetzner DNS"),
]

# Env vars that signal a DNS provider is pre-configured.
# Order matters: first match wins for pre-selection.
_DNS_ENV_HINTS: list[tuple[str, str]] = [
    ("CLOUDFLARE_API_TOKEN",     "cloudflare"),
    ("TF_VAR_cloudflare_api_token", "cloudflare"),
    ("TF_VAR_do_token",          "digitalocean"),
    ("TF_VAR_hcloud_token",      "hetzner"),
]

# Env var name for each DNS provider's token
_DNS_TOKEN_ENV: dict[str, str] = {
    "cloudflare":   "TF_VAR_cloudflare_api_token",
    "digitalocean": "TF_VAR_do_token",
    "hetzner":      "TF_VAR_hcloud_token",  # same token as compute
}

CSS = """
HubSpinupScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.info { color: $text-muted; margin: 0 1 1 1; }
.status-ok  { color: $success; margin: 0 1; }
.status-bad { color: $error;   margin: 0 1; }
.field-row { height: 3; margin: 0 1; }
#provider-select { margin: 0 1 1 1; }
#dns-provider-select { margin: 0 1 1 1; }
#log { height: 20; border: solid $primary; margin: 1; }
#apply-btn { margin: 1; }
#back-btn  { margin: 0 0 1 1; }
"""


def _tf_binary() -> str:
    """Return 'terraform' if available, else 'tofu'.

    HashiCorp Terraform is preferred because it has access to providers that
    only exist in the Terraform registry (e.g. timohirt/hetznerdns).
    """
    return "terraform" if shutil.which("terraform") else "tofu"


def _token_env_var(provider: str) -> str:
    """Return the TF_VAR_* environment variable name for the compute provider."""
    return "TF_VAR_hcloud_token" if provider == "hetzner" else "TF_VAR_do_token"


def _detect_dns_provider() -> str:
    """Return the DNS provider slug pre-selected from env, or 'none'."""
    for env_var, slug in _DNS_ENV_HINTS:
        if os.environ.get(env_var):
            return slug
    return "none"


def _detect_dns_token(dns_provider: str) -> str:
    """Return a pre-filled DNS token from env for the given provider, or ''."""
    if dns_provider == "none":
        return ""
    env_var = _DNS_TOKEN_ENV.get(dns_provider, "")
    # Also check the bare CLOUDFLARE_API_TOKEN convention
    if dns_provider == "cloudflare":
        return os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get(env_var, "")
    return os.environ.get(env_var, "")


class HubSpinupScreen(Screen):
    """Provision the hub VPS via terraform apply + ansible-playbook."""

    TITLE = "Step 3b: Hub Spinup"
    CSS = CSS

    def __init__(self, endpoint: str = "") -> None:
        super().__init__()
        self._endpoint = endpoint
        self._hub_hostname = endpoint.split(":")[0] if endpoint else ""
        self._running = False

    def compose(self) -> ComposeResult:
        tf = _tf_binary()
        tf_ok = shutil.which(tf) is not None
        ansible_ok = shutil.which("ansible-playbook") is not None
        ansible_dir_ok = ANSIBLE_DIR.exists()

        # Detect pre-set compute token (hcloud preferred)
        env_token = (
            os.environ.get("TF_VAR_hcloud_token")
            or os.environ.get("TF_VAR_do_token")
            or ""
        )
        token_hint = "(pre-set from environment)" if env_token else ""

        # Detect pre-set DNS provider + token
        default_dns_provider = _detect_dns_provider()
        dns_env_token = _detect_dns_token(default_dns_provider)
        dns_token_hint = "(pre-set from environment)" if dns_env_token else ""

        yield Header()
        yield ScrollableContainer(
            Label("Cloud provider", classes="section-title"),
            Select(
                [(label, value) for value, label in PROVIDER_OPTIONS],
                value="hetzner",
                id="provider-select",
            ),
            Label("Tool availability", classes="section-title"),
            Static(
                "\n".join([
                    f"{'[green]✓[/]' if tf_ok else '[red]✗[/]'}  {tf}",
                    f"{'[green]✓[/]' if ansible_ok else '[red]✗[/]'}  ansible-playbook",
                    f"{'[green]✓[/]' if ansible_dir_ok else '[red]✗[/]'}  ansible/ directory",
                ]),
                markup=True,
                classes="info",
                id="tool-status",
            ),
            Label("Terraform directory", classes="section-title"),
            Label("", id="tf-dir-label", classes="info"),
            Label("Hub hostname", classes="section-title"),
            Label(
                "Fully-qualified hostname for the hub (e.g. hub.example.com).",
                classes="info",
            ),
            Vertical(
                Input(
                    value=self._hub_hostname,
                    placeholder="hub.example.com",
                    id="hostname-input",
                ),
                classes="field-row",
            ),
            Label("Compute API token", classes="section-title"),
            Label(
                "Hetzner Cloud or DigitalOcean token for provisioning the server. "
                "Set TF_VAR_hcloud_token or TF_VAR_do_token in your environment, or paste below.",
                classes="info",
            ),
            Label(token_hint, id="token-hint", classes="info"),
            Vertical(
                Input(
                    value=env_token,
                    placeholder="paste token (or leave blank if env var is set)",
                    password=True,
                    id="token-input",
                ),
                classes="field-row",
            ),
            Label("DNS provider", classes="section-title"),
            Label(
                "Which DNS provider holds your domain zone? "
                "Select 'None' to skip DNS and manage records manually.",
                classes="info",
            ),
            Select(
                [(label, value) for value, label in DNS_PROVIDER_OPTIONS],
                value=default_dns_provider,
                id="dns-provider-select",
            ),
            Label("DNS API token", classes="section-title"),
            Label(
                "Token for the selected DNS provider. Not required when DNS provider is 'None' "
                "or when the Hetzner DNS provider is selected (reuses the compute token).",
                classes="info",
            ),
            Label(dns_token_hint, id="dns-token-hint", classes="info"),
            Vertical(
                Input(
                    value=dns_env_token,
                    placeholder="paste DNS token (leave blank if not needed or env var is set)",
                    password=True,
                    id="dns-token-input",
                ),
                classes="field-row",
            ),
            RichLog(id="log", highlight=True, markup=True),
        )
        yield Button(
            f"Apply ({tf} + ansible-playbook)",
            id="apply-btn",
            variant="primary",
            disabled=not (tf_ok and ansible_ok and ansible_dir_ok),
        )
        yield Button("← Back", id="back-btn", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_tf_dir_label("hetzner")
        self._refresh_dns_token_state(_detect_dns_provider())

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @on(Select.Changed, "#provider-select")
    def _provider_changed(self, event: Select.Changed) -> None:
        self._refresh_tf_dir_label(str(event.value))

    @on(Select.Changed, "#dns-provider-select")
    def _dns_provider_changed(self, event: Select.Changed) -> None:
        self._refresh_dns_token_state(str(event.value))

    def _refresh_tf_dir_label(self, provider: str) -> None:
        tf_dir = PROVIDER_DIRS.get(provider, Path("terraform"))
        exists = tf_dir.exists()
        icon = "[green]✓[/]" if exists else "[red]✗[/]"
        try:
            self.query_one("#tf-dir-label", Label).update(
                f"{icon}  {tf_dir}/", markup=True
            )
        except Exception:  # noqa: BLE001
            pass

    def _refresh_dns_token_state(self, dns_provider: str) -> None:
        """Update DNS token field: hide for 'none'/'hetzner', pre-fill for others."""
        dns_token_input = self.query_one("#dns-token-input", Input)
        dns_token_hint = self.query_one("#dns-token-hint", Label)

        if dns_provider in ("none", "hetzner"):
            # No separate DNS token needed
            dns_token_input.value = ""
            dns_token_input.placeholder = "not required for this DNS provider"
            dns_token_hint.update("")
        else:
            pre = _detect_dns_token(dns_provider)
            dns_token_input.value = pre
            dns_token_input.placeholder = "paste DNS token (or set env var)"
            dns_token_hint.update("(pre-set from environment)" if pre else "")

    @on(Button.Pressed, "#back-btn")
    def _back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#apply-btn")
    def _apply(self) -> None:
        if self._running:
            return
        hostname = self.query_one("#hostname-input", Input).value.strip()
        token = self.query_one("#token-input", Input).value.strip()
        provider_val = self.query_one("#provider-select", Select).value
        provider = str(provider_val) if provider_val is not Select.BLANK else "hetzner"

        dns_val = self.query_one("#dns-provider-select", Select).value
        dns_provider = str(dns_val) if dns_val is not Select.BLANK else "none"
        dns_token = self.query_one("#dns-token-input", Input).value.strip()

        if not hostname:
            self._log("[bold red]✗ Hub hostname is required[/]")
            return
        tf_dir = PROVIDER_DIRS.get(provider, Path("terraform"))
        if not tf_dir.exists():
            self._log(f"[bold red]✗ Terraform directory not found: {tf_dir}/[/]")
            return
        self._running = True
        self.query_one("#apply-btn", Button).disabled = True
        self._run_spinup(hostname, token, provider, tf_dir, dns_provider, dns_token)  # type: ignore[unused-coroutine]

    # ------------------------------------------------------------------
    # Spinup worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_spinup(
        self,
        hostname: str,
        token: str,
        provider: str,
        tf_dir: Path,
        dns_provider: str,
        dns_token: str,
    ) -> None:
        log = self.query_one("#log", RichLog)
        tf = _tf_binary()

        env = os.environ.copy()
        env["TF_VAR_hub_hostname"] = hostname
        env["TF_VAR_dns_provider"] = dns_provider
        env["TF_IN_AUTOMATION"] = "1"

        if token:
            env[_token_env_var(provider)] = token

        if dns_token and dns_provider not in ("none", "hetzner"):
            env[_DNS_TOKEN_ENV[dns_provider]] = dns_token

        # --- terraform init ---
        log.write(f"[bold]$ {tf} init   # in {tf_dir}/[/]")
        rc = await self._stream(log, [tf, "init"], cwd=str(tf_dir), env=env)
        if rc != 0:
            self._finish(log, success=False, msg=f"{tf} init failed (exit {rc})")
            return

        # --- terraform apply ---
        log.write(f"\n[bold]$ {tf} apply -auto-approve[/]")
        rc = await self._stream(
            log, [tf, "apply", "-auto-approve"], cwd=str(tf_dir), env=env
        )
        if rc != 0:
            self._finish(log, success=False, msg=f"{tf} apply failed (exit {rc})")
            return

        # --- get hub IP from output ---
        proc = await asyncio.create_subprocess_exec(
            tf, "output", "-raw", "hub_ip",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(tf_dir),
            env=env,
        )
        ip_bytes, err_bytes = await proc.communicate()
        hub_ip = ip_bytes.decode().strip()
        if proc.returncode != 0 or not hub_ip:
            err = err_bytes.decode().strip()
            self._finish(log, success=False, msg=f"Could not get hub_ip output: {err}")
            return
        log.write(f"\n[bold green]✓ Hub IP: {hub_ip}[/]")

        # --- ansible-playbook ---
        log.write(f"\n[bold]$ ansible-playbook site.yml -e hub_ip={hub_ip}[/]")
        rc = await self._stream(
            log,
            ["ansible-playbook", "site.yml", "-e", f"hub_ip={hub_ip}"],
            cwd=str(ANSIBLE_DIR),
            env=env,
        )
        if rc != 0:
            self._finish(log, success=False, msg=f"ansible-playbook failed (exit {rc})")
            return

        self._finish(log, success=True, msg=f"Hub provisioned at {hub_ip} — returning to hub check")

    async def _stream(
        self,
        log: RichLog,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> int:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=env,
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

    def _finish(self, log: RichLog, *, success: bool, msg: str) -> None:
        self._running = False
        self.query_one("#apply-btn", Button).disabled = False
        if success:
            log.write(f"\n[bold green]✓ {msg}[/]")
            self.app.pop_screen()
        else:
            log.write(f"\n[bold red]✗ {msg}[/]")

    def _log(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)
