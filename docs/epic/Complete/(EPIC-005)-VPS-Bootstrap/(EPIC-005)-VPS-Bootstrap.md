---
artifact: EPIC-005
title: VPS Bootstrap & Disaster Recovery
status: Complete
author: cristos
created: 2026-02-28
last-updated: 2026-03-03
parent-vision: VISION-001
depends-on:
  - EPIC-002
---

# EPIC-005: VPS Bootstrap & Disaster Recovery

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 6405885 | Initial creation, merged from external project |
| Active | 2026-03-03 | 812ef39 | porthole bootstrap command implemented; VPS runtime testing pending |
| Complete | 2026-03-03 | eaa69bf | porthole bootstrap: apt, CoreDNS, Docker, configs, services fully scripted |

---

## Goal

Automate the full provisioning of a VPS from bare Ubuntu to functioning WireGuard relay hub. This is the disaster recovery path: if the VPS is destroyed, the operator clones the encrypted repo, points at a new VPS, and runs one command to rebuild. It is also the initial setup path for the first deployment.

## Success criteria

- `porthole sync --full` against a fresh Ubuntu VPS installs WireGuard, CoreDNS, enables IP forwarding, deploys all configs, and brings up the network.
- Full rebuild from clone-to-connected takes under 10 minutes.
- VPS runs no services beyond WireGuard, CoreDNS, SSH, and the status script.
- The bootstrap process is idempotent — running it twice produces the same result.

## Scope boundaries

**In scope:**

- `porthole sync --full` command that performs complete VPS setup via SSH
- Install WireGuard, enable `net.ipv4.ip_forward`, configure firewall (UFW or iptables)
- Install and configure CoreDNS with the `.wg` zone
- Deploy the hub WireGuard config and enable `wg-quick@wg0`
- Deploy the status script
- Idempotent execution — safe to re-run
- Targeting Ubuntu 22.04+ (or whatever the chosen VPS provider offers)

**Out of scope:**

- Multi-cloud or multi-provider orchestration
- VPS procurement automation (the operator manually creates the VPS)
- Cloud-init (SSH-based provisioning is simpler and doesn't depend on provider support)
- Monitoring or alerting setup on the VPS (operator runs Uptime Kuma separately)

## Child artifacts

_Updated as Agent Specs are created._

## Key dependencies

- EPIC-002 for network state, config templates, and the `sync` command infrastructure
- A fresh VPS with SSH access and a public IP
- The age private key available on the operator's workstation
