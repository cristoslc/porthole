"""Generate per-peer watchdog and tunnel service files."""
from __future__ import annotations

from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from porthole import config, state
from porthole.config import TEMPLATE_DIR


def run_gen_peer_scripts(peer_name: str, out_dir: Path) -> None:
    """Render watchdog and tunnel service templates for a specific peer."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    peer = next((p for p in network.peers if p.name == peer_name), None)
    if peer is None:
        raise click.ClickException(f"Peer '{peer_name}' not found")
    if peer.role == "hub":
        raise click.ClickException("Hub does not need client-side scripts")

    hub_peer = next(p for p in network.peers if p.role == "hub")
    hub_endpoint_host = network.hub.endpoint.split(":")[0]
    hub_public_ip = hub_endpoint_host  # DNS name — tunnel connects directly

    out_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR / "peer-scripts")),
        keep_trailing_newline=True,
    )

    is_windows = getattr(peer, "platform", None) == "windows"

    # Files rendered for all platforms
    files: dict[str, str] = {
        "wg-watchdog.sh": "wg-watchdog.sh.j2",
        "wg-watchdog.service": "wg-watchdog.service.j2",
        "wg-watchdog.timer": "wg-watchdog.timer.j2",
        "wg-watchdog.plist": "wg-watchdog.plist.j2",
        f"ssh-tunnel-{peer_name}.service": "ssh-tunnel.service.j2",
        f"ssh-tunnel-{peer_name}.plist": "ssh-tunnel.plist.j2",
        "wg-status-server.py": "wg-status-server.py.j2",
        "wg-status-server.service": "wg-status-server.service.j2",
        "wg-status-server.plist": "wg-status-server.plist.j2",
    }

    # Windows-specific files
    if is_windows:
        files["wg-watchdog.ps1"] = "wg-watchdog.ps1.j2"
        files[f"wg-watchdog-task-{peer_name}.xml"] = "wg-watchdog-task.xml.j2"

    ctx = dict(
        peer=peer,
        hub=hub_peer,
        hub_endpoint_host=hub_endpoint_host,
        hub_public_ip=hub_public_ip,
    )

    for filename, template_name in files.items():
        template = env.get_template(template_name)
        rendered = template.render(**ctx)
        out_path = out_dir / filename
        out_path.write_text(rendered)
        click.echo(f"  {out_path}")

    # Make scripts executable (Linux/macOS only)
    (out_dir / "wg-watchdog.sh").chmod(0o755)
    (out_dir / "wg-status-server.py").chmod(0o755)

    click.echo(f"\nGenerated {len(files)} files in {out_dir}/")
    click.echo("\nInstall on Linux:")
    click.echo(f"  sudo cp wg-watchdog.sh wg-status-server.py /usr/local/bin/")
    click.echo(f"  sudo cp wg-watchdog.service wg-watchdog.timer /etc/systemd/system/")
    click.echo(f"  sudo cp ssh-tunnel-{peer_name}.service wg-status-server.service /etc/systemd/system/")
    click.echo(f"  sudo systemctl daemon-reload")
    click.echo(f"  sudo systemctl enable --now wg-watchdog.timer ssh-tunnel-{peer_name}.service wg-status-server.service")
    click.echo(f"\nInstall on macOS:")
    click.echo(f"  sudo cp wg-watchdog.sh wg-status-server.py /usr/local/bin/")
    click.echo(f"  sudo cp wg-watchdog.plist /Library/LaunchDaemons/")
    click.echo(f"  sudo cp ssh-tunnel-{peer_name}.plist /Library/LaunchDaemons/")
    click.echo(f"  sudo cp wg-status-server.plist /Library/LaunchDaemons/")
    click.echo(f"  sudo launchctl load -w /Library/LaunchDaemons/com.porthole.watchdog.{peer_name}.plist")
    click.echo(f"  sudo launchctl load -w /Library/LaunchDaemons/com.porthole.tunnel.{peer_name}.plist")
    click.echo(f"  sudo launchctl load -w /Library/LaunchDaemons/com.porthole.status.{peer_name}.plist")
    if is_windows:
        click.echo(f"\nInstall on Windows (run PowerShell as Administrator):")
        click.echo(f"  New-Item -ItemType Directory -Force -Path C:\\ProgramData\\Porthole")
        click.echo(f"  Copy-Item wg-watchdog.ps1 C:\\ProgramData\\Porthole\\wg-watchdog.ps1")
        click.echo(f"  schtasks /Create /TN \"Porthole\\wg-watchdog-{peer_name}\" /XML wg-watchdog-task-{peer_name}.xml /F")
    click.echo(f"\nStatus UI: http://<lan-ip>:8888/ (auto-starts on boot)")
