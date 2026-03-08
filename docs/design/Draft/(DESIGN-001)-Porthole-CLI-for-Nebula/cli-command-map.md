# CLI Command Reference

**Supporting doc for:** [DESIGN-001](./(DESIGN-001)-Porthole-CLI-for-Nebula.md)

## Command inventory

### `porthole init`

| Aspect | Details |
|--------|---------|
| Purpose | Initialize a new Nebula network — create CA, sign lighthouse cert, write encrypted state |
| Arguments | `--endpoint` (lighthouse public hostname), `--age-key` (path to age key), `--domain` (DNS zone, default `wg`) |
| External tools | `nebula-cert ca`, `nebula-cert sign`, `sops` |
| Output | `network.sops.yaml` containing CA cert/key, lighthouse cert/key, network config |
| Steps | 1. `nebula-cert ca -name "porthole-ca"` → CA keypair. 2. `nebula-cert sign -name "lighthouse" -ip "10.100.0.1/24" -groups "lighthouse"` → lighthouse cert. 3. Write state file, encrypt with SOPS. |

### `porthole add`

| Aspect | Details |
|--------|---------|
| Purpose | Enroll a new peer — sign certificate, allocate IP, update state |
| Arguments | `name` (required), `--role` (workstation/server/family), `--platform` (linux/macos/windows), `--dns-name` (CoreDNS hostname), `--groups` (Nebula cert groups, defaults from role) |
| External tools | `nebula-cert sign` |
| Output | Updated `network.sops.yaml` with new peer entry |
| Steps | 1. Decrypt state to access CA key. 2. Allocate next IP from subnet pool. 3. `nebula-cert sign -name "<name>" -ip "<ip>/24" -groups "<groups>"`. 4. Append peer to state, re-encrypt. |
| Note | No hub/lighthouse interaction required. The lighthouse discovers this peer when it connects with its signed certificate. |

### `porthole remove`

| Aspect | Details |
|--------|---------|
| Purpose | Remove a peer from the network and revoke its certificate |
| Arguments | `name` (required) |
| External tools | None (state-only operation) |
| Output | Updated `network.sops.yaml` with peer removed and cert fingerprint on blocklist |
| Steps | 1. Remove peer entry from state. 2. Add peer's cert fingerprint to blocklist. 3. Re-encrypt state. |
| Note | Blocklist takes effect on lighthouse after `porthole deploy-lighthouse`. Without deployment, the peer's cert expires naturally at its configured duration. |

### `porthole list`

| Aspect | Details |
|--------|---------|
| Purpose | Display all enrolled peers |
| Arguments | `--json` (machine-readable output) |
| External tools | None |
| Output | Table: name, overlay IP, DNS name, role, platform, groups |

### `porthole peer-config`

| Aspect | Details |
|--------|---------|
| Purpose | Render a complete Nebula config bundle for a peer |
| Arguments | `name` (required), `--out` (output directory) |
| External tools | Jinja2 template engine |
| Output | Config bundle: `config.yml` + `ca.crt` + `<name>.crt` + `<name>.key` |
| Template | `peer-config.yml.j2` → `config.yml` |
| Install location | Linux/macOS: `/etc/nebula/` (4 files). Windows: `C:\Program Files\Nebula\` |

### `porthole gen-peer-scripts`

| Aspect | Details |
|--------|---------|
| Purpose | Generate platform-appropriate service files for running nebula |
| Arguments | `name` (required), `--out` (output directory) |
| External tools | Jinja2 template engine |
| Output | Service unit files: systemd unit (Linux), launchd plist (macOS), or Windows service installer |
| Note | Single service per node — nebula handles reconnection natively via `punchy`. Optional SSH tunnel service available as add-on (SPIKE-006 Layer 2). |

### `porthole install-peer`

| Aspect | Details |
|--------|---------|
| Purpose | Deploy config bundle and service to a peer via SSH |
| Arguments | `name` (required), `--host` (SSH target) |
| External tools | `scp`, `ssh` |
| Steps | 1. SCP config bundle to peer's nebula config directory. 2. Install service unit. 3. Enable and start nebula service. |

### `porthole enroll`

| Aspect | Details |
|--------|---------|
| Purpose | Transfer config bundle to a target peer |
| Arguments | `name` (required), `--manual` (skip wormhole, output file path) |
| External tools | Magic Wormhole (default mode) |
| Bundle contents | `ca.crt`, `<name>.crt`, `<name>.key`, `config.yml` |
| Default mode | Generate a one-time wormhole code. Operator enters code on target peer to receive bundle. |
| Manual mode | Write bundle to local directory, output path for manual transfer (USB, SCP, etc.) |

### `porthole bootstrap`

| Aspect | Details |
|--------|---------|
| Purpose | Provision the lighthouse on a fresh VPS |
| Arguments | `hub_host` (required) |
| External tools | `terraform`, `ansible-playbook` |
| Steps | 1. `terraform apply` — create VPS, configure DNS, open UDP port. 2. `ansible-playbook` — install nebula lighthouse + CoreDNS + Guacamole Docker stack. |
| Cloud-init payload | Nebula binary, lighthouse config, CA cert, lighthouse cert/key, CoreDNS config |
| Services deployed | `nebula` (lighthouse mode), CoreDNS, Guacamole (Docker) |

### `porthole status`

| Aspect | Details |
|--------|---------|
| Purpose | Show live peer connectivity status from the lighthouse |
| Arguments | None |
| External tools | `ssh` (to lighthouse) |
| Data source | SSH to lighthouse → nebula admin API |
| Fields | Peer name, overlay IP, certificate groups, last handshake, relay status, connection type |

### `porthole dashboard`

| Aspect | Details |
|--------|---------|
| Purpose | Run a local web dashboard showing fleet status |
| Arguments | `--port` (HTTP listen port) |
| External tools | None |
| Output | HTTP server serving fleet status page |

### `porthole seed-guac`

| Aspect | Details |
|--------|---------|
| Purpose | Generate Guacamole connection seed SQL from peer state |
| Arguments | `--out` (SQL output path), `--apply` (execute against Guacamole DB) |
| External tools | None (reads state, generates SQL) |
| Output | SQL INSERT statements mapping peer IPs to Guacamole connections |

### `porthole deploy-lighthouse`

| Aspect | Details |
|--------|---------|
| Purpose | Push updated lighthouse config to the hub (blocklist changes, DNS zone updates) |
| Arguments | None |
| External tools | `ansible-playbook` |
| When needed | After `porthole remove` (to deploy blocklist for immediate cert revocation), or after DNS zone changes |

## External tool dependencies

| Tool | Used by | Purpose |
|------|---------|---------|
| `nebula-cert` | `init`, `add` | CA creation (`ca`) and peer cert signing (`sign`) |
| `nebula` | Peer service | Overlay network binary (systemd/launchd unit) |
| `sops` + `age` | All state operations | Encrypt/decrypt `network.sops.yaml` |
| `terraform` | `bootstrap` | VPS provisioning |
| `ansible-playbook` | `bootstrap`, `deploy-lighthouse` | Configuration deployment |
| `ssh` + `scp` | `status`, `install-peer` | Remote access to lighthouse and peers |
| `wormhole` | `enroll` | Zero-config file transfer for config bundles |
| Jinja2 | `peer-config`, `gen-peer-scripts`, `bootstrap` | Template rendering |
