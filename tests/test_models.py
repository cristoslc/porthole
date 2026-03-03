from wgmesh.models import HubConfig, Network, Peer


class TestPeer:
    def test_to_dict_minimal(self):
        peer = Peer(
            name="hub", ip="10.100.0.1",
            public_key="pub", private_key="priv",
            dns_name="hub", role="hub",
        )
        d = peer.to_dict()
        assert d["name"] == "hub"
        assert "reverse_ssh_port" not in d

    def test_to_dict_with_port(self):
        peer = Peer(
            name="laptop", ip="10.100.0.2",
            public_key="pub", private_key="priv",
            dns_name="laptop", role="workstation",
            reverse_ssh_port=2202,
        )
        d = peer.to_dict()
        assert d["reverse_ssh_port"] == 2202

    def test_roundtrip(self):
        peer = Peer(
            name="laptop", ip="10.100.0.2",
            public_key="pub", private_key="priv",
            dns_name="laptop", role="workstation",
            reverse_ssh_port=2202,
        )
        assert Peer.from_dict(peer.to_dict()) == peer


class TestNetwork:
    def test_to_dict_structure(self, sample_network):
        d = sample_network.to_dict()
        assert "network" in d
        assert d["network"]["domain"] == "wg"
        assert d["network"]["subnet"] == "10.100.0.0/24"
        assert len(d["network"]["peers"]) == 3

    def test_roundtrip(self, sample_network):
        d = sample_network.to_dict()
        restored = Network.from_dict(d)
        assert restored.domain == sample_network.domain
        assert restored.subnet == sample_network.subnet
        assert restored.hub.endpoint == sample_network.hub.endpoint
        assert len(restored.peers) == len(sample_network.peers)
        for orig, rest in zip(sample_network.peers, restored.peers):
            assert orig == rest
