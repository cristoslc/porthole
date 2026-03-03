from wgmesh.render import render_hub_config, render_peer_config, render_dns_zone, render_nftables


class TestRenderHubConfig:
    def test_contains_interface(self, hub_peer, sample_peers, sample_network):
        spoke_peers = [p for p in sample_peers if p.role != "hub"]
        result = render_hub_config(hub_peer, spoke_peers, sample_network)

        assert "[Interface]" in result
        assert "10.100.0.1/24" in result
        assert "ListenPort = 51820" in result
        assert hub_peer.private_key in result

    def test_contains_peer_stanzas(self, hub_peer, sample_peers, sample_network):
        spoke_peers = [p for p in sample_peers if p.role != "hub"]
        result = render_hub_config(hub_peer, spoke_peers, sample_network)

        assert "[Peer]" in result
        assert "desktop-linux" in result
        assert "desktop-pub-key-base64=" in result
        assert "10.100.0.2/32" in result
        assert "mom-imac" in result


class TestRenderPeerConfig:
    def test_contains_interface_and_peer(self, hub_peer, sample_peers):
        peer = sample_peers[1]  # desktop-linux
        result = render_peer_config(peer, hub_peer, "hub.example.com:51820")

        assert "[Interface]" in result
        assert "10.100.0.2/24" in result
        assert peer.private_key in result
        assert "[Peer]" in result
        assert hub_peer.public_key in result
        assert "hub.example.com:51820" in result
        assert "PersistentKeepalive = 25" in result


class TestRenderDnsZone:
    def test_contains_all_peers(self, sample_network):
        result = render_dns_zone(sample_network)

        assert "$ORIGIN wg." in result
        assert "SOA" in result
        assert "hub" in result
        assert "10.100.0.1" in result
        assert "desktop-linux" in result
        assert "10.100.0.2" in result
        assert "mom-imac" in result
        assert "10.100.0.10" in result


class TestRenderNftables:
    def test_contains_firewall_rules(self, sample_network):
        result = render_nftables(sample_network)

        assert "flush ruleset" in result
        assert "udp dport 51820 accept" in result
        assert "tcp dport 22 accept" in result
        assert "wg0" in result
        assert sample_network.subnet in result
