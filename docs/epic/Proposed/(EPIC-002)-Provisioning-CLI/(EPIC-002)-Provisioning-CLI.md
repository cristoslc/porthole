# EPIC-002: Provisioning CLI & Network State Management

**Status:** Proposed
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 6405885 | Initial creation, merged from external project |

---

## Goal

Build the core CLI tool that manages the full lifecycle of a WireGuard relay network: initialization, peer provisioning, peer removal, state encryption, and deployment to the VPS hub. This is the foundation everything else builds on — the repo-as-source-of-truth pattern that makes disaster recovery and reproducibility possible.

## Success criteria

- Operator can `wgmesh init` to bootstrap a new network with subnet, hub config, and SOPS-encrypted state file.
- Operator can `wgmesh add <name>` to generate keys, assign IP, register DNS, and output a deployable client config.
- Operator can `wgmesh remove <name>` to revoke a peer and regenerate hub config.
- Operator can `wgmesh sync` to push current hub WireGuard config and DNS zone to VPS via SSH without downtime.
- All private keys in `network.sops.yaml` are encrypted with age; public keys, IPs, and names may be cleartext or encrypted.
- Project runs via `uv run wgmesh` with no pre-installed dependencies beyond uv itself.

## Scope boundaries

**In scope:**

- `init` command: create `network.sops.yaml` with subnet, hub endpoint, hub key pair, `.sops.yaml` config
- `add` command: generate WireGuard key pair, assign next available IP from subnet, add peer to state file, output client wg config
- `remove` command: remove peer from state file, flag IP as reclaimable
- `sync` command: render hub WireGuard config and DNS zone from state, push to VPS via SSH, hot-reload with `wg syncconf` and CoreDNS reload
- `list` command: display current peers with IPs and DNS names
- `status` command: SSH to VPS, run `wg show`, format and display peer status
- SOPS/age encryption of the state file
- Jinja2 templating for WireGuard configs and DNS zones
- Python project managed with uv, runnable as `uv run wgmesh`

**Out of scope:**

- Client web UI (EPIC-003)
- Dashboard / monitoring (EPIC-004)
- VPS bootstrap / cloud-init automation (EPIC-005)
- Automated config distribution to client machines

## Child artifacts

_Updated as Agent Specs are created._

## Key dependencies

- uv must be available on the operator's workstation
- age key must exist for SOPS encryption/decryption
- SSH access to the VPS with key-based auth
- WireGuard and CoreDNS installed on the VPS (see EPIC-005 for automation)
