from ipaddress import IPv4Address, IPv4Network
from pathlib import Path

DEFAULT_SUBNET = IPv4Network("10.100.0.0/24")
HUB_IP = IPv4Address("10.100.0.1")
WG_PORT = 51820
REVERSE_SSH_BASE = 2200
STATE_FILE = Path("network.sops.yaml")
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
DEFAULT_DOMAIN = "wg"
