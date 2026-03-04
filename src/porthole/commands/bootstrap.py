"""Bootstrap a fresh Ubuntu VPS to a functioning WireGuard hub."""
import click

from porthole import config, render, ssh, state

COREDNS_VERSION = "1.11.3"
COREDNS_ARCH = "amd64"

BOOTSTRAP_SCRIPT = """\
set -e

# --- Package installation ---
apt-get update -qq
apt-get install -y -qq wireguard wireguard-tools nftables curl

# --- IPv4 forwarding ---
sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-wg.conf

# --- CoreDNS ---
if ! command -v coredns >/dev/null 2>&1; then
    COREDNS_VER={coredns_version}
    ARCH={arch}
    URL="https://github.com/coredns/coredns/releases/download/v${{COREDNS_VER}}/coredns_${{COREDNS_VER}}_linux_${{ARCH}}.tgz"
    curl -sL "$URL" | tar -C /usr/local/bin -xz coredns
    chmod +x /usr/local/bin/coredns
fi
mkdir -p /etc/coredns

# --- CoreDNS systemd service ---
cat > /etc/systemd/system/coredns.service << 'EOF'
[Unit]
Description=CoreDNS DNS server
After=network.target

[Service]
ExecStart=/usr/local/bin/coredns -conf /etc/coredns/Corefile
Restart=always
RestartSec=5
LimitNOFILE=1048576
LimitNPROC=512

[Install]
WantedBy=multi-user.target
EOF

# --- Docker (for Guacamole) ---
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
fi

# --- Enable services ---
systemctl daemon-reload
systemctl enable coredns
systemctl enable nftables

echo "Bootstrap complete"
""".strip()


def run_bootstrap(hub_host: str) -> None:
    """Bootstrap a fresh Ubuntu VPS to a functioning WireGuard hub."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)
    hub_peer = next(p for p in network.peers if p.role == "hub")
    spoke_peers = [p for p in network.peers if p.role != "hub"]

    # Step 1: Run package/service bootstrap
    click.echo(f"Bootstrapping {hub_host}...")
    script = BOOTSTRAP_SCRIPT.format(
        coredns_version=COREDNS_VERSION,
        arch=COREDNS_ARCH,
    )
    ssh.ssh_run(hub_host, script)
    click.echo("Packages installed and services configured")

    # Step 2: Deploy WireGuard config
    hub_wg = render.render_hub_config(hub_peer, spoke_peers, network)
    ssh.scp_to_host(hub_host, hub_wg, "/etc/wireguard/wg0.conf")
    click.echo("Deployed wg0.conf")

    # Step 3: Deploy CoreDNS Corefile and zone
    corefile = render.render_corefile(network, hub_ip=str(config.HUB_IP))
    ssh.scp_to_host(hub_host, corefile, "/etc/coredns/Corefile")
    zone = render.render_dns_zone(network)
    ssh.scp_to_host(hub_host, zone, "/etc/coredns/wg.zone")
    click.echo("Deployed CoreDNS config")

    # Step 4: Deploy nftables
    nft = render.render_nftables(network)
    ssh.scp_to_host(hub_host, nft, "/etc/nftables.conf")
    click.echo("Deployed nftables.conf")

    # Step 5: Enable and start
    ssh.ssh_run(hub_host, (
        "systemctl enable --now wg-quick@wg0 && "
        "systemctl restart coredns && "
        "nft -f /etc/nftables.conf"
    ))
    click.echo("Services started")
    click.echo("Hub bootstrap complete — WireGuard + CoreDNS + nftables running")
