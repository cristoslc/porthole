import click

from porthole import config, state


def run_remove(name: str) -> None:
    """Remove a peer from the mesh network."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    if name == "hub":
        raise click.ClickException("Cannot remove the hub peer")

    peer = next((p for p in network.peers if p.name == name), None)
    if peer is None:
        raise click.ClickException(f"Peer '{name}' not found")

    network.peers = [p for p in network.peers if p.name != name]
    state.save_state(network, state_path)
    click.echo(f"Removed peer '{name}' ({peer.ip})")
