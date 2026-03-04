"""Output the WireGuard config for a single peer."""
from __future__ import annotations

from pathlib import Path

import click

from porthole import config, render, state


def run_peer_config(name: str, out_path: Path | None) -> None:
    """Render and output the WireGuard config for a peer."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    peer = next((p for p in network.peers if p.name == name), None)
    if peer is None:
        raise click.ClickException(f"Peer '{name}' not found")
    if peer.role == "hub":
        raise click.ClickException("Hub does not need a peer config")

    hub_peer = next(p for p in network.peers if p.role == "hub")
    conf = render.render_peer_config(peer, hub_peer, network.hub.endpoint)

    if out_path:
        out_path.write_text(conf)
        out_path.chmod(0o600)
        click.echo(f"Written to {out_path}")
    else:
        click.echo(conf, nl=False)
