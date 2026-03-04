from ipaddress import IPv4Address, IPv4Network

from porthole.config import REVERSE_SSH_BASE


def next_available_ip(subnet: str, allocated: list[str]) -> IPv4Address | None:
    """Return the next available IP in the subnet, skipping .0 (network), .1 (hub), and .255 (broadcast)."""
    network = IPv4Network(subnet)
    allocated_set = {IPv4Address(ip) for ip in allocated}

    for host in network.hosts():
        # Skip .1 (reserved for hub)
        if host == network.network_address + 1:
            continue
        if host not in allocated_set:
            return host
    return None


def reverse_ssh_port(ip: str) -> int:
    """Calculate reverse SSH port from IP: 2200 + last octet."""
    last_octet = int(IPv4Address(ip).packed[-1])
    return REVERSE_SSH_BASE + last_octet
