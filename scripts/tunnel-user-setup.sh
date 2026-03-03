#!/usr/bin/env bash
# tunnel-user-setup.sh — Run on the VPS to create the restricted tunnel user.
# This is a one-time setup. Re-running is safe (idempotent).
# Usage: sudo bash tunnel-user-setup.sh

set -euo pipefail

TUNNEL_USER="tunnel"

# Create user with no home directory, no login shell
if ! id "$TUNNEL_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$TUNNEL_USER"
    echo "Created user: $TUNNEL_USER"
else
    echo "User $TUNNEL_USER already exists"
fi

# Create .ssh directory
SSH_DIR="/home/${TUNNEL_USER}/.ssh"
mkdir -p "$SSH_DIR"

# We need a home dir for .ssh — override:
usermod -d "/home/${TUNNEL_USER}" "$TUNNEL_USER"
mkdir -p "/home/${TUNNEL_USER}/.ssh"
chown -R "${TUNNEL_USER}:${TUNNEL_USER}" "/home/${TUNNEL_USER}"
chmod 700 "/home/${TUNNEL_USER}/.ssh"
touch "/home/${TUNNEL_USER}/.ssh/authorized_keys"
chmod 600 "/home/${TUNNEL_USER}/.ssh/authorized_keys"

echo ""
echo "Tunnel user setup complete."
echo ""
echo "Next steps:"
echo "  1. For each peer, generate a tunnel SSH key (wgmesh gen-peer-scripts <name>)"
echo "  2. Add each peer's public key to /home/${TUNNEL_USER}/.ssh/authorized_keys"
echo "     with the following prefix to restrict to port-forwarding only:"
echo ""
echo '     command="/bin/false",no-pty,no-agent-forwarding,no-X11-forwarding,permitopen="none" ssh-ed25519 AAAA... peer-name'
echo ""
echo "  3. Update nftables to allow TCP 2200-2220 inbound:"
echo "     (wgmesh bootstrap or wgmesh sync handles this via nftables.conf.j2)"
