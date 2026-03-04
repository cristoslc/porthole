"""Generate Guacamole connection seed SQL from network state."""
import click
from jinja2 import Environment, FileSystemLoader

from porthole import config, state
from porthole.config import TEMPLATE_DIR


def run_seed_guac(out_file) -> None:
    """Generate SQL to seed Guacamole connections from network.sops.yaml."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)
    spoke_peers = [p for p in network.peers if p.role != "hub"]

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("guacamole-seed.sql.j2")
    sql = template.render(peers=spoke_peers)

    if out_file:
        out_file.write(sql)
    else:
        click.echo(sql)
