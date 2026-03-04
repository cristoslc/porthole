import json

import click

from porthole import config, state


def run_list(as_json: bool) -> None:
    """List all peers in the mesh network."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    if as_json:
        peers = []
        for p in network.peers:
            entry = {
                "name": p.name,
                "ip": p.ip,
                "dns": f"{p.dns_name}.{network.domain}",
                "role": p.role,
            }
            if p.reverse_ssh_port is not None:
                entry["reverse_ssh_port"] = p.reverse_ssh_port
            peers.append(entry)
        click.echo(json.dumps(peers, indent=2))
        return

    # Table output
    header = f"{'NAME':<20} {'IP':<16} {'DNS':<25} {'ROLE':<12} {'REV SSH':<8}"
    click.echo(header)
    click.echo("-" * len(header))
    for p in network.peers:
        dns = f"{p.dns_name}.{network.domain}"
        rev = str(p.reverse_ssh_port) if p.reverse_ssh_port is not None else "-"
        click.echo(f"{p.name:<20} {p.ip:<16} {dns:<25} {p.role:<12} {rev:<8}")
