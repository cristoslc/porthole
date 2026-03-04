import secrets

import click

from porthole import config, keys, models, sops, state


def run_init(endpoint: str, age_key: str) -> None:
    """Initialize a new mesh network with hub as the first peer."""
    state_path = config.STATE_FILE
    if state_path.exists():
        raise click.ClickException(f"State file already exists: {state_path}")

    sops.create_sops_config(age_key)
    click.echo("Created .sops.yaml")

    private_key, public_key = keys.generate_keypair()
    click.echo("Generated hub keypair")

    guacamole_admin_password = secrets.token_urlsafe(24)

    hub_peer = models.Peer(
        name="hub",
        ip=str(config.HUB_IP),
        public_key=public_key,
        private_key=private_key,
        dns_name="hub",
        role="hub",
    )
    hub_config = models.HubConfig(
        endpoint=endpoint,
    )
    network = models.Network(
        hub=hub_config,
        peers=[hub_peer],
        guacamole_admin_password=guacamole_admin_password,
    )

    state.save_state(network, state_path)
    click.echo(f"Initialized network state: {state_path}")
    click.echo("Guacamole admin password generated and stored (encrypted in state)")
