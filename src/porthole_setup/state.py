"""Read and parse porthole network state from network.sops.yaml."""
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class StateNotFoundError(FileNotFoundError):
    """Raised when network.sops.yaml does not exist."""


class StateDecryptionError(RuntimeError):
    """Raised when sops cannot decrypt network.sops.yaml."""


@dataclass
class Peer:
    name: str
    ip: str
    public_key: str
    role: str = ""


@dataclass
class NetworkState:
    endpoint: str
    peers: list[Peer] = field(default_factory=list)

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    def get_peer(self, name: str) -> Peer | None:
        return next((p for p in self.peers if p.name == name), None)


def load_state(state_file: Path = Path("network.sops.yaml")) -> NetworkState:
    """
    Decrypt and parse network.sops.yaml. Returns a NetworkState.

    Raises:
        StateNotFoundError: if the file does not exist.
        StateDecryptionError: if sops cannot decrypt it.
        ValueError: if the decrypted content cannot be parsed.
    """
    if not state_file.exists():
        raise StateNotFoundError(f"State file not found: {state_file}")

    try:
        result = subprocess.run(
            ["sops", "-d", "--output-type", "json", str(state_file)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise StateDecryptionError(
            f"sops failed to decrypt {state_file}: {exc.stderr}"
        ) from exc

    data = json.loads(result.stdout)

    net = data.get("network", data)  # support both wrapped and flat formats
    hub = net.get("hub", {})
    endpoint = hub.get("endpoint", net.get("endpoint", ""))

    peers = [
        Peer(
            name=p["name"],
            ip=p.get("ip", ""),
            public_key=p.get("public_key", ""),
            role=p.get("role", ""),
        )
        for p in net.get("peers", [])
    ]

    return NetworkState(
        endpoint=endpoint,
        peers=peers,
    )
