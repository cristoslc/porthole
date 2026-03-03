from pathlib import Path
from unittest.mock import patch

import yaml

from wgmesh.models import HubConfig, Network, Peer
from wgmesh.state import load_state, save_state


class TestSaveState:
    @patch("wgmesh.state.encrypt_file")
    def test_writes_yaml_and_encrypts(self, mock_encrypt, tmp_path):
        state_path = tmp_path / "network.sops.yaml"
        network = Network(
            hub=HubConfig(endpoint="hub.example.com:51820"),
            peers=[
                Peer(
                    name="hub", ip="10.100.0.1",
                    public_key="pub", private_key="priv",
                    dns_name="hub", role="hub",
                ),
            ],
        )

        save_state(network, state_path)

        # File should exist with YAML content before encryption
        assert state_path.exists()
        data = yaml.safe_load(state_path.read_text())
        assert data["network"]["hub"]["endpoint"] == "hub.example.com:51820"
        assert len(data["network"]["peers"]) == 1
        assert data["network"]["peers"][0]["name"] == "hub"

        mock_encrypt.assert_called_once_with(state_path)


class TestLoadState:
    @patch("wgmesh.state.decrypt_file")
    def test_decrypts_and_parses(self, mock_decrypt):
        mock_decrypt.return_value = yaml.dump({
            "network": {
                "domain": "wg",
                "subnet": "10.100.0.0/24",
                "hub": {"endpoint": "hub.example.com:51820"},
                "peers": [
                    {
                        "name": "hub", "ip": "10.100.0.1",
                        "public_key": "pub", "private_key": "priv",
                        "dns_name": "hub", "role": "hub",
                    },
                    {
                        "name": "laptop", "ip": "10.100.0.2",
                        "public_key": "pub2", "private_key": "priv2",
                        "dns_name": "laptop", "role": "workstation",
                        "reverse_ssh_port": 2202,
                    },
                ],
            }
        })

        network = load_state(Path("test.sops.yaml"))

        assert network.domain == "wg"
        assert network.subnet == "10.100.0.0/24"
        assert network.hub.endpoint == "hub.example.com:51820"
        assert len(network.peers) == 2
        assert network.peers[1].name == "laptop"
        assert network.peers[1].reverse_ssh_port == 2202
