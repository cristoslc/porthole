# CLI Command Map: WireGuard → Nebula

**Supporting doc for:** [DESIGN-001](./(DESIGN-001)-Porthole-CLI-and-TUI-for-Nebula.md)

## Command-by-command migration

### `porthole init`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Key generation | `wg genkey \| wg pubkey` → hub keypair | `nebula-cert ca` → CA keypair; `nebula-cert sign` → lighthouse cert |
| State created | Hub peer with WG public/private key | CA cert+key, lighthouse cert+key, network config |
| Flags | `--endpoint`, `--age-key`, `--domain` | Same flags, same UX |
| External tool | `wg` | `nebula-cert` |
| Output | `network.sops.yaml` with hub entry | `network.sops.yaml` with CA + lighthouse entry |

### `porthole add`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Key generation | `wg genkey \| wg pubkey` → peer keypair | `nebula-cert sign` → peer cert (signed by CA key) |
| IP allocation | Next available in subnet | Same |
| Hub update needed? | **YES** — must run `porthole sync` after | **NO** — lighthouse discovers peer from cert |
| Groups | Not used by WG | `--groups workstation` maps to Nebula cert groups |
| External tool | `wg` | `nebula-cert` |

### `porthole sync` — ELIMINATED

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Purpose | SSH to hub, push wg0.conf + DNS zone + nftables, reload services | **Not needed.** Lighthouse discovers peers from their certificates. |
| DNS zone | Pushed via SSH + sync | Pushed via Ansible during initial provisioning; updated via `porthole deploy-dns` if needed |
| Firewall | nftables rules pushed via SSH | Nebula firewall rules are in lighthouse config, deployed during provisioning |

**Migration note:** The only remaining case where hub config needs updating is certificate revocation (adding to blocklist). This is handled by `porthole remove` + `porthole deploy-lighthouse` (Ansible).

### `porthole remove`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| State update | Remove peer from state | Remove peer from state + add cert fingerprint to blocklist |
| Hub update needed? | **YES** — must run `porthole sync` after | **Optional** — `porthole deploy-lighthouse` to push blocklist for immediate revocation; without it, cert expires naturally |
| External tool | None (state only) | None (state only) |

### `porthole peer-config`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Output | Single `wg0.conf` file | Config bundle: `config.yml` + `ca.crt` + `<name>.crt` + `<name>.key` |
| Template | `peer-wg0.conf.j2` | `peer-config.yml.j2` |
| Install location | `/etc/wireguard/wg0.conf` | `/etc/nebula/` (4 files) |

### `porthole gen-peer-scripts`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Services generated | wg-quick + watchdog timer + SSH tunnel + status server | nebula service (single unit) + optional SSH tunnel |
| Templates | 11 templates across 3 platforms | ~4 templates (systemd, launchd, Windows service, optional SSH tunnel) |
| Watchdog | Complex: DNS re-resolve, WG reload, handshake check | Simple: check nebula process, restart if needed |

### `porthole bootstrap`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Packages | wireguard, nftables, coredns, docker | nebula, coredns, docker |
| Config | wg0.conf, nftables.conf, Corefile, zone | lighthouse config.yml, ca.crt, lighthouse cert/key, Corefile, zone |
| Firewall | nftables rules deployed separately | Nebula firewall in lighthouse config |
| Services | wg-quick@wg0, nftables, coredns, docker | nebula (lighthouse), coredns, docker |

### `porthole status`

| Aspect | WireGuard (old) | Nebula (new) |
|--------|----------------|--------------|
| Data source | SSH to hub → `wg show wg0 dump` | SSH to lighthouse → nebula status / admin API |
| Fields | Public key, endpoint, last handshake, Tx/Rx | Peer name, IP, groups, last handshake, relay status |

### `porthole enroll` — NEW

| Aspect | Details |
|--------|---------|
| Purpose | Transfer config bundle to target peer |
| Methods | Magic Wormhole (default), `--manual` (output file path) |
| Bundle contents | `ca.crt`, `<name>.crt`, `<name>.key`, `config.yml` |
| Replaces | Ad-hoc `porthole peer-config \| scp` pattern |

### `porthole deploy-lighthouse` — NEW

| Aspect | Details |
|--------|---------|
| Purpose | Push updated lighthouse config to hub (blocklist, DNS zone changes) |
| Method | Ansible playbook targeting lighthouse host |
| When needed | After `porthole remove` (blocklist update), or DNS zone changes |
| Replaces | `porthole sync` (but much rarer — only for revocation/DNS, not every peer add) |

### Unchanged commands

| Command | Notes |
|---------|-------|
| `porthole list` | Reads state, displays table. No WireGuard-specific logic. |
| `porthole dashboard` | HTTP server, reads status data. Adapts to new status format. |
| `porthole seed-guac` | Reads peer IPs from state, generates SQL. Tunnel-agnostic. |
| `porthole install-peer` | SCP + service enable. Changes service names, not the flow. |

## External tool changes

| Old tool | New tool | Used by |
|----------|----------|---------|
| `wg` (genkey, pubkey) | `nebula-cert` (ca, sign) | `init`, `add` |
| `wg` (show dump) | nebula admin API or SSH status | `status`, `dashboard` |
| `wg-quick` | `nebula` binary | Service management on peers |
| `nft` / `nftables` | Nebula built-in firewall | Eliminated from hub config |
| `sops`, `age` | `sops`, `age` | Unchanged |
| `terraform` | `terraform` | Unchanged |
| `ansible-playbook` | `ansible-playbook` | Unchanged |
| `ssh`, `scp` | `ssh`, `scp` | Unchanged (but used less — no sync) |
