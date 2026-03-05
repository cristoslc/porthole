from __future__ import annotations

import click

from porthole import config, keys, models, render, state, subnet


def run_add(name: str, role: str, platform: str | None = None, dns_name: str | None = None) -> None:
    """Add a new peer to the mesh network."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path} (run 'porthole init' first)")

    network = state.load_state(state_path)

    for peer in network.peers:
        if peer.name == name:
            raise click.ClickException(f"Peer '{name}' already exists")

    allocated_ips = [p.ip for p in network.peers]
    ip = subnet.next_available_ip(network.subnet, allocated_ips)
    if ip is None:
        raise click.ClickException("No available IPs in subnet")

    private_key, public_key = keys.generate_keypair()
    reverse_port = subnet.reverse_ssh_port(ip)

    peer = models.Peer(
        name=name,
        ip=str(ip),
        public_key=public_key,
        private_key=private_key,
        dns_name=dns_name or name,
        role=role,
        reverse_ssh_port=reverse_port,
        platform=platform,
    )
    network.peers.append(peer)
    state.save_state(network, state_path)
    click.echo(f"Added peer '{name}' ({ip})")

    hub_peer = next(p for p in network.peers if p.role == "hub")
    peer_conf = render.render_peer_config(peer, hub_peer, network.hub.endpoint)
    click.echo("\n--- Peer WireGuard config ---")
    click.echo(peer_conf)
