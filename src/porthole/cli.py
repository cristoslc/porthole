import click

from porthole import __version__


@click.group()
@click.version_option(version=__version__, prog_name="porthole")
def cli():
    """WireGuard hub-and-spoke mesh network manager."""


@cli.command()
@click.option("--endpoint", required=True, help="Hub endpoint (e.g. hub.example.com:51820)")
@click.option("--age-key", required=True, help="Age public key for SOPS encryption")
def init(endpoint, age_key):
    """Initialize a new mesh network."""
    from porthole.commands.init import run_init

    run_init(endpoint, age_key)


@cli.command()
@click.argument("name")
@click.option("--role", default="workstation", type=click.Choice(["workstation", "server", "family"]),
              help="Peer role (default: workstation)")
@click.option("--platform", default=None, type=click.Choice(["linux", "macos", "windows"]),
              help="OS platform — controls Guacamole protocol (linux=xrdp, macos=vnc, windows=rdp)")
def add(name, role, platform):
    """Add a new peer to the mesh network."""
    from porthole.commands.add import run_add

    run_add(name, role, platform)


@cli.command()
@click.argument("name")
def remove(name):
    """Remove a peer from the mesh network."""
    from porthole.commands.remove import run_remove

    run_remove(name)


@cli.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_peers(as_json):
    """List all peers in the mesh network."""
    from porthole.commands.list_cmd import run_list

    run_list(as_json)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Print rendered configs without deploying")
def sync(dry_run):
    """Sync hub configuration to the VPS."""
    from porthole.commands.sync import run_sync

    run_sync(dry_run)


@cli.command("gen-peer-scripts")
@click.argument("peer_name")
@click.option("--out", "out_dir", type=click.Path(), default=None,
              help="Output directory (default: peer-scripts/<name>/)")
def gen_peer_scripts(peer_name, out_dir):
    """Generate watchdog + tunnel service files for a peer."""
    from pathlib import Path
    from porthole.commands.gen_peer_scripts import run_gen_peer_scripts

    directory = Path(out_dir) if out_dir else Path(f"peer-scripts/{peer_name}")
    run_gen_peer_scripts(peer_name, directory)


@cli.command("seed-guac")
@click.option("--out", "out_file", type=click.File("w"), default=None,
              help="Write SQL to file instead of stdout")
@click.option("--apply", is_flag=True, help="Apply SQL directly to the hub's Guacamole database via SSH")
def seed_guac(out_file, apply):
    """Generate Guacamole connection seed SQL from network state."""
    from porthole.commands.seed_guac import run_seed_guac

    run_seed_guac(out_file, apply)


@cli.command("peer-config")
@click.argument("name")
@click.option("--out", "out_path", type=click.Path(), default=None,
              help="Write config to file (chmod 600)")
def peer_config(name, out_path):
    """Output the WireGuard config for a peer."""
    from pathlib import Path
    from porthole.commands.peer_config import run_peer_config

    run_peer_config(name, Path(out_path) if out_path else None)


@cli.command("install-peer")
@click.argument("name")
@click.option("--host", default=None,
              help="SSH target host/IP (default: peer's WireGuard IP for linux peers)")
def install_peer(name, host):
    """Generate and optionally install peer scripts via SSH."""
    from porthole.commands.install_peer import run_install_peer

    run_install_peer(name, host)


@cli.command()
@click.argument("hub_host")
def bootstrap(hub_host):
    """Bootstrap a fresh Ubuntu VPS to a functioning WireGuard hub."""
    from porthole.commands.bootstrap import run_bootstrap

    run_bootstrap(hub_host)


@cli.command()
def status():
    """Show live WireGuard peer status from the hub."""
    from porthole.commands.status import run_status

    run_status()


@cli.command()
@click.option("--port", default=8080, show_default=True, help="Port to listen on")
def dashboard(port):
    """Run a local web dashboard showing fleet peer status."""
    from porthole.commands.dashboard import run_dashboard

    run_dashboard(port)
