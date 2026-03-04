import click

from porthole import config, ssh, state


def run_status() -> None:
    """Show live WireGuard peer status from the hub."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)
    hub_host = network.hub.endpoint.split(":")[0]

    output = ssh.ssh_run(hub_host, "wg show wg0 dump")

    # Build pubkey -> peer name map
    key_map = {p.public_key: p for p in network.peers if p.role != "hub"}

    lines = output.strip().splitlines()
    if len(lines) < 2:
        click.echo("No peers connected.")
        return

    header = f"{'NAME':<20} {'IP':<16} {'ENDPOINT':<25} {'LATEST HANDSHAKE':<20} {'TX':<12} {'RX':<12}"
    click.echo(header)
    click.echo("-" * len(header))

    # Skip first line (interface line)
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) < 8:
            continue
        pubkey = fields[0]
        endpoint = fields[2] if fields[2] != "(none)" else "-"
        latest_handshake = fields[4]
        tx = fields[5]
        rx = fields[6]

        peer = key_map.get(pubkey)
        name = peer.name if peer else f"unknown ({pubkey[:8]}...)"
        ip = peer.ip if peer else "-"

        # Format handshake timestamp
        if latest_handshake == "0":
            hs_display = "never"
        else:
            import datetime

            hs_time = datetime.datetime.fromtimestamp(int(latest_handshake))
            hs_display = hs_time.strftime("%Y-%m-%d %H:%M:%S")

        # Format bytes
        tx_display = _format_bytes(int(tx))
        rx_display = _format_bytes(int(rx))

        click.echo(f"{name:<20} {ip:<16} {endpoint:<25} {hs_display:<20} {tx_display:<12} {rx_display:<12}")


def _format_bytes(b: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if b < 1024:
            return f"{b:.1f} {unit}" if unit != "B" else f"{b} {unit}"
        b /= 1024
    return f"{b:.1f} TiB"
