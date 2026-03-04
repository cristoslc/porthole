"""Install WireGuard tunnel and watchdog scripts on a peer via SSH."""
from __future__ import annotations

from pathlib import Path

import click

from porthole import config, render, state, ssh
from porthole.commands.gen_peer_scripts import run_gen_peer_scripts

_LINUX_INSTALL = """\
# Copy to peer and run:
sudo cp wg-watchdog.sh wg-status-server.py /usr/local/bin/
sudo chmod +x /usr/local/bin/wg-watchdog.sh /usr/local/bin/wg-status-server.py
sudo cp wg-watchdog.service wg-watchdog.timer /etc/systemd/system/
sudo cp ssh-tunnel-{name}.service wg-status-server.service /etc/systemd/system/
sudo install -m 600 wg0.conf /etc/wireguard/wg0.conf
sudo systemctl daemon-reload
sudo systemctl enable --now wg-quick@wg0 wg-watchdog.timer ssh-tunnel-{name}.service wg-status-server.service"""


def run_install_peer(name: str, ssh_host: str | None) -> None:
    """Generate peer scripts and optionally install them via SSH."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    peer = next((p for p in network.peers if p.name == name), None)
    if peer is None:
        raise click.ClickException(f"Peer '{name}' not found")
    if peer.role == "hub":
        raise click.ClickException("Hub does not use peer install scripts")

    hub_peer = next(p for p in network.peers if p.role == "hub")

    out_dir = Path(f"peer-scripts/{name}")
    run_gen_peer_scripts(name, out_dir)

    # Also write wg0.conf alongside the scripts
    conf = render.render_peer_config(peer, hub_peer, network.hub.endpoint)
    wg_conf_path = out_dir / "wg0.conf"
    wg_conf_path.write_text(conf)
    wg_conf_path.chmod(0o600)
    click.echo(f"  {wg_conf_path}")

    target = ssh_host or (peer.ip if peer.platform == "linux" else None)

    if target:
        click.echo(f"\nInstalling via SSH to {target}...")
        _install_linux(name, out_dir, target)
    else:
        click.echo(f"\nScripts saved to {out_dir}/")
        if peer.platform == "macos":
            click.echo("\nSee gen-peer-scripts output above for macOS install steps.")
        else:
            click.echo("\n" + _LINUX_INSTALL.format(name=name))
        click.echo(f"\nOr install directly: porthole install-peer {name} --host <IP>")


def _install_linux(name: str, out_dir: Path, target: str) -> None:
    """Upload and activate peer scripts on a Linux peer via SSH."""
    ssh.scp_to_host(target, (out_dir / "wg0.conf").read_text(), "/etc/wireguard/wg0.conf")
    ssh.ssh_run(target, "chmod 600 /etc/wireguard/wg0.conf")
    click.echo("  Uploaded /etc/wireguard/wg0.conf")

    for script in ("wg-watchdog.sh", "wg-status-server.py"):
        ssh.scp_to_host(target, (out_dir / script).read_text(), f"/usr/local/bin/{script}")
        ssh.ssh_run(target, f"chmod +x /usr/local/bin/{script}")
        click.echo(f"  Uploaded /usr/local/bin/{script}")

    for unit in ("wg-watchdog.service", "wg-watchdog.timer", "wg-status-server.service"):
        ssh.scp_to_host(target, (out_dir / unit).read_text(), f"/etc/systemd/system/{unit}")
        click.echo(f"  Uploaded /etc/systemd/system/{unit}")

    tunnel_unit = f"ssh-tunnel-{name}.service"
    ssh.scp_to_host(target, (out_dir / tunnel_unit).read_text(), f"/etc/systemd/system/{tunnel_unit}")
    click.echo(f"  Uploaded /etc/systemd/system/{tunnel_unit}")

    ssh.ssh_run(target, "systemctl daemon-reload")
    ssh.ssh_run(
        target,
        f"systemctl enable --now wg-quick@wg0 wg-watchdog.timer ssh-tunnel-{name}.service wg-status-server.service",
    )
    click.echo(f"\nEnabled: wg-quick@wg0, wg-watchdog.timer, ssh-tunnel-{name}.service, wg-status-server.service")
    click.echo(f"\nInstall complete. Peer '{name}' should connect shortly.")
