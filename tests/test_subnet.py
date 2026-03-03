from wgmesh.subnet import next_available_ip, reverse_ssh_port


class TestNextAvailableIP:
    def test_first_allocation_skips_hub(self):
        ip = next_available_ip("10.100.0.0/24", ["10.100.0.1"])
        assert str(ip) == "10.100.0.2"

    def test_skips_allocated(self):
        allocated = ["10.100.0.1", "10.100.0.2", "10.100.0.3"]
        ip = next_available_ip("10.100.0.0/24", allocated)
        assert str(ip) == "10.100.0.4"

    def test_fills_gaps(self):
        allocated = ["10.100.0.1", "10.100.0.2", "10.100.0.4"]
        ip = next_available_ip("10.100.0.0/24", allocated)
        assert str(ip) == "10.100.0.3"

    def test_returns_none_when_exhausted(self):
        # /30 gives .0 (network), .1 (hub), .2, .3 (broadcast)
        # Only .2 is a usable host after hub
        allocated = ["10.100.0.1", "10.100.0.2"]
        ip = next_available_ip("10.100.0.0/30", allocated)
        assert ip is None

    def test_never_assigns_hub_ip(self):
        ip = next_available_ip("10.100.0.0/24", [])
        # .1 is skipped (hub), so first allocation is .2
        # But .1 isn't in allocated, so it's "available" in the sense
        # of hosts() iteration. Our function skips .1 explicitly.
        assert str(ip) == "10.100.0.2"


class TestReverseSSHPort:
    def test_port_for_ip(self):
        assert reverse_ssh_port("10.100.0.2") == 2202

    def test_port_for_high_octet(self):
        assert reverse_ssh_port("10.100.0.250") == 2450

    def test_port_for_hub(self):
        assert reverse_ssh_port("10.100.0.1") == 2201
