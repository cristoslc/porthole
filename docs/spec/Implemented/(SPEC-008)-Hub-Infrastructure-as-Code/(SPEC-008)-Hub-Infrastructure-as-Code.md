---
title: "Hub Infrastructure as Code"
artifact: SPEC-008
status: Implemented
author: cristos
created: 2026-03-03
last-updated: 2026-03-04
parent-epic: EPIC-007
linked-research:
  - SPIKE-007
linked-adrs:
  - ADR-006
depends-on: []
addresses:
  - JOURNEY-004.PP-01
---

# SPEC-008: Hub Infrastructure as Code

**Status:** Implemented
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [EPIC-007](../../../epic/Proposed/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft    | 2026-03-03 | 2ec07f7 | Initial creation |
| Approved     | 2026-03-04 | 79b2e76 | 7 gaps identified; implementation plan created in bd |
| Implemented  | 2026-03-04 | eb16a5f | backend.tf (both providers), DO firewall ports, Guacamole schema init + seed execution + platform-aware template, guacamole_db_password in group_vars |

---

## Problem Statement

The current `porthole bootstrap` command provisions the hub by SSHing into the VPS
and running inline shell scripts. This works for first-time setup but:

- Is not reproducible — scripts are not idempotent and have no state tracking.
- Is not version-controlled as infrastructure — the "desired state" lives in
  Python source, not in declarative IaC.
- Cannot rebuild the hub from scratch reliably after destruction.
- Requires manual DNS setup outside the tool.

SPIKE-007 validated that the hub should be treated as ephemeral: destroyed and
rebuilt from `network.sops.yaml` and repo state on demand. The current bootstrap
approach does not support this model.

## External Behavior

### Inputs

| Input | Source |
|-------|--------|
| Cloud provider credentials | Environment variables (provider-specific) |
| Hub endpoint hostname | Terraform variable or `network.sops.yaml` |
| `network.sops.yaml` | porthole state file; decrypted at Ansible runtime |
| Age private key | `~/.config/sops/age/keys.txt` (standard SOPS location) |

### Outputs

| Output | Description |
|--------|-------------|
| Running VPS | Provisioned with public IP, SSH access, correct firewall |
| DNS A record | Hub hostname resolves to VPS public IP |
| WireGuard server | `wg0` up, all enrolled peers in config |
| CoreDNS | `*.wg` zone resolving from porthole state |
| nftables | Isolation rules applied |
| Guacamole | Running via Docker Compose, bound to WireGuard interface |
| Caddy | TLS termination via DNS-01 challenge |
| Tunnel user | `tunnel` OS user created; `authorized_keys` populated from state |

### Constraints

- Destroying and re-running (`terraform destroy && terraform apply`) must produce
  a fully functional hub within 10 minutes, with no manual steps.
- Ansible playbook must be idempotent: re-running against an already-configured
  hub changes nothing and exits cleanly.
- All secrets remain encrypted at rest (SOPS/age); Ansible decrypts at runtime.
- The Terraform provider is a configurable input; DigitalOcean is the reference
  implementation. The Ansible playbook is provider-agnostic.

## Acceptance Criteria

- **Given** a fresh cloud account with credentials in environment variables,
  **when** `terraform apply` completes, **then** a VPS exists with a public IP
  and an SSH-accessible `root` user, and the hub's DNS A record resolves.

- **Given** a provisioned VPS and a valid `network.sops.yaml`,
  **when** `ansible-playbook site.yml` completes, **then** WireGuard, CoreDNS,
  nftables, Guacamole, Caddy, and the tunnel user are all running and configured
  from state.

- **Given** a fully configured hub,
  **when** `ansible-playbook site.yml` is run again with no state changes,
  **then** the playbook exits with 0 changes and 0 failures.

- **Given** a destroyed and freshly re-provisioned VPS with the same
  `network.sops.yaml`,
  **when** the Ansible playbook runs, **then** existing enrolled nodes can
  re-establish WireGuard connections without any changes on the node side.

- **Given** a new peer added via `porthole add <name> && porthole sync`,
  **when** the Ansible playbook runs against the hub, **then** the new peer's
  WireGuard config and CoreDNS entry are present on the hub.

- **Given** the operator is working from a different machine than the one
  originally used to provision the hub (e.g., the original workstation is
  unavailable), **when** `terraform apply` is run, **then** Terraform retrieves
  existing state from the remote backend and does not create duplicate resources.

## Scope & Constraints

**In scope:**
- `terraform/` directory with provider config, VPS resource, DNS record, and
  firewall/security group rules.
- `ansible/` directory with a hub playbook covering all hub services.
- Ansible reads porthole state (decrypted via SOPS) to populate WireGuard peers,
  CoreDNS zone, and tunnel `authorized_keys`.
- Terraform state backend: the `terraform/` and `terraform-hetzner/` directories
  MUST include a `backend.tf` that configures a remote state backend. The
  reference implementation uses Terraform Cloud (HCP) as the backend — it is
  free for small teams and eliminates the risk of losing `terraform.tfstate`
  when the operator's workstation is unavailable. A local backend with a clearly
  documented backup path is acceptable as a fallback.
  **Rationale**: without remote state, a hub rebuild from a different machine
  (e.g., if the original workstation is also unavailable) leaves Terraform with
  no record of existing resources, risking orphaned DNS records, firewall rules,
  or duplicate server charges (addresses JOURNEY-004.PP-01).

**Not in scope:**
- Multi-region or multi-hub deployments.
- Ansible-based node configuration (nodes use porthole CLI + service file templates).
- Windows support.
- Terraform provider implementations beyond the reference (DigitalOcean).

**`porthole bootstrap` disposition:** The command remains in place during the
transition but is a candidate for deprecation once SPEC-008 is validated. The
two approaches are not mutually exclusive in the interim.

## Implementation Approach

```
terraform/
  main.tf          VPS resource, SSH key, firewall
  dns.tf           A record for hub hostname
  outputs.tf       Public IP, VPS ID
  variables.tf     Provider, region, size, SSH key, hostname
  versions.tf      Terraform + provider version pins

ansible/
  site.yml         Hub playbook (imports roles in order)
  inventory.yml    Dynamic or static; hub IP from Terraform output
  group_vars/
    hub.yml        Non-secret vars (WireGuard port, interface, subnet)
  roles/
    wireguard/     Install wg-quick, render wg0.conf from state
    coredns/       Install binary, render Corefile + wg.zone from state
    nftables/      Install, render and apply rules from state
    guacamole/     Docker Compose up, seed connections from state
    caddy/         Install, render Caddyfile, start
    tunnel-user/   Create user, populate authorized_keys from state
```

State integration: a custom Ansible module or `lookup` plugin decrypts
`network.sops.yaml` and exposes it as a variable dict for use in role templates.
This replaces the per-role Jinja2 rendering currently done by the porthole CLI.
