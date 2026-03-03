import pytest

from wgmesh.models import HubConfig, Network, Peer


@pytest.fixture
def hub_peer():
    return Peer(
        name="hub",
        ip="10.100.0.1",
        public_key="hub-pub-key-base64=",
        private_key="hub-priv-key-base64=",
        dns_name="hub",
        role="hub",
    )


@pytest.fixture
def sample_peers(hub_peer):
    return [
        hub_peer,
        Peer(
            name="desktop-linux",
            ip="10.100.0.2",
            public_key="desktop-pub-key-base64=",
            private_key="desktop-priv-key-base64=",
            dns_name="desktop-linux",
            role="workstation",
            reverse_ssh_port=2202,
        ),
        Peer(
            name="mom-imac",
            ip="10.100.0.10",
            public_key="mom-pub-key-base64=",
            private_key="mom-priv-key-base64=",
            dns_name="mom-imac",
            role="family",
            reverse_ssh_port=2210,
        ),
    ]


@pytest.fixture
def sample_network(sample_peers):
    return Network(
        hub=HubConfig(endpoint="hub.example.com:51820"),
        peers=sample_peers,
    )
