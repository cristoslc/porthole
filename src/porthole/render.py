from __future__ import annotations

from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from porthole.config import TEMPLATE_DIR
from porthole.models import Network, Peer


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )


def render_hub_config(hub: Peer, spoke_peers: list[Peer], network: Network) -> str:
    """Render the hub WireGuard config."""
    env = _env()
    template = env.get_template("hub-wg0.conf.j2")
    return template.render(hub=hub, peers=spoke_peers, network=network)


def render_peer_config(peer: Peer, hub: Peer, endpoint: str) -> str:
    """Render an individual peer WireGuard config."""
    env = _env()
    template = env.get_template("peer-wg0.conf.j2")
    return template.render(peer=peer, hub=hub, endpoint=endpoint, subnet="10.100.0.0/24")


def render_dns_zone(network: Network) -> str:
    """Render the CoreDNS zone file for the .wg domain."""
    env = _env()
    template = env.get_template("coredns-wg.zone.j2")
    serial = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    return template.render(network=network, serial=serial)


def render_nftables(network: Network) -> str:
    """Render the nftables firewall config for the hub."""
    env = _env()
    template = env.get_template("nftables.conf.j2")
    return template.render(network=network)


def render_corefile(network: Network, hub_ip: str) -> str:
    """Render the CoreDNS Corefile."""
    env = _env()
    template = env.get_template("coredns-Corefile.j2")
    return template.render(network=network, hub_ip=hub_ip)
