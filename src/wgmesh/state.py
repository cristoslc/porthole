from pathlib import Path

import yaml

from wgmesh.models import Network
from wgmesh.sops import decrypt_file, encrypt_file


def load_state(path: Path) -> Network:
    """Load and decrypt the network state file."""
    plaintext = decrypt_file(path)
    data = yaml.safe_load(plaintext)
    return Network.from_dict(data)


def save_state(network: Network, path: Path) -> None:
    """Serialize network state to YAML and encrypt with SOPS."""
    data = network.to_dict()
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    encrypt_file(path)
