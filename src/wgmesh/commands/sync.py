import click

from wgmesh import config, render, ssh, state


def run_sync(dry_run: bool) -> None:
    """Sync hub configuration to the VPS."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)
    hub_peer = next(p for p in network.peers if p.role == "hub")
    spoke_peers = [p for p in network.peers if p.role != "hub"]

    hub_wg_conf = render.render_hub_config(hub_peer, spoke_peers, network)
    zone_file = render.render_dns_zone(network)
    nft_conf = render.render_nftables(network)

    if dry_run:
        click.echo("=== hub wg0.conf ===")
        click.echo(hub_wg_conf)
        click.echo("\n=== coredns wg zone ===")
        click.echo(zone_file)
        click.echo("\n=== nftables.conf ===")
        click.echo(nft_conf)
        return

    # Determine hub SSH target from endpoint (host part)
    hub_host = network.hub.endpoint.split(":")[0]

    ssh.scp_to_host(hub_host, hub_wg_conf, "/etc/wireguard/wg0.conf")
    click.echo("Uploaded wg0.conf")

    ssh.scp_to_host(hub_host, zone_file, "/etc/coredns/wg.zone")
    click.echo("Uploaded wg zone file")

    ssh.scp_to_host(hub_host, nft_conf, "/etc/nftables.conf")
    click.echo("Uploaded nftables.conf")

    # Reload services
    ssh.ssh_run(hub_host, "wg syncconf wg0 <(wg-quick strip /etc/wireguard/wg0.conf)")
    click.echo("Reloaded WireGuard config")

    ssh.ssh_run(hub_host, "systemctl reload coredns")
    click.echo("Reloaded CoreDNS")

    ssh.ssh_run(hub_host, "nft -f /etc/nftables.conf")
    click.echo("Applied nftables rules")

    click.echo("Sync complete.")
