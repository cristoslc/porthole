---
title: "WireGuard bootstrap without SSH — minimize exposure with age-encrypted setup key"
artifact: SPIKE-009
status: Active
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
question: "Can we bootstrap a WireGuard hub VPS without permanent public SSH, using cloud-init for first boot and an age-encrypted setup-only SSH key for ongoing management?"
gate: "Pre-MVP"
risks-addressed:
  - "SSH exposure on hub VPS during provisioning window"
  - "Ansible dependency for hub bootstrap adds complexity and failure modes"
  - "SSH keys for provisioning conflated with guacamole access credentials"
depends-on: []
---

# WireGuard bootstrap without SSH

## Question

Can we bootstrap a WireGuard hub VPS without permanent public SSH, and handle spoke N+1 enrollment securely? Is something like Pangolin a good base, or are there simpler composable building blocks?

## Go / No-Go Criteria

- **Go:** A proven approach exists using only boring, stable technology (cloud-init, SSH, age, Terraform) that: (a) eliminates permanent public SSH on the hub, (b) handles spoke N+1 enrollment without a coordination server, (c) requires no vendor lock-in or risky dependencies.
- **No-Go:** All viable approaches require a coordination server, ecosystem lock-in, or custom enrollment services.

## Pivot Recommendation

If cloud-init WireGuard support is unreliable across providers: fall back to standard SSH provisioning with key-only auth, `AllowUsers`, and fail2ban. SSH is boring and proven — the exposure is well-understood and manageable.

## Findings

### Pangolin — not suitable

Pangolin is an identity-aware remote access platform (reverse proxy + VPN), not a WireGuard orchestrator. AGPL-3.0 with commercial restrictions. 19.4k GitHub stars. You adopt the full ecosystem or nothing.

**Verdict:** Solves a different problem. Not composable.

### Coordination servers — overkill

| Solution | License | Stars | Requires | Lock-in |
|----------|---------|-------|----------|---------|
| Headscale | BSD-3 | 36.2k | Headscale server + Tailscale clients | Tailscale protocol |
| Netmaker | Apache 2.0 | 11.5k | Netmaker server + Docker | Netmaker client |
| NetBird | BSD-3/AGPL-3 | 23.3k | Mgmt + Signal + STUN/TURN | NetBird agent |
| innernet | MIT | 5.4k | innernet server | innernet client |
| Nebula | MIT | 17.1k | Lighthouse | Not WireGuard at all |

All require running additional infrastructure and lock you into their client ecosystem. Overkill for hub-and-spoke.

### The spoke N+1 problem

Cloud-init's native WireGuard module can bootstrap the hub at first boot — WireGuard is up before SSH. But spoke N+1 isn't on the WireGuard network yet. To update the hub's peer list (`porthole sync`), you need a management channel to the hub. Options:

1. **Coordination server** — Headscale/Netmaker/etc. Adds infrastructure and lock-in.
2. **HTTPS enrollment API on the hub** — Custom code. Maintenance burden.
3. **SSH from an existing spoke** — Only works if the provisioning workstation is already on the network.
4. **SSH over public internet** — Simple, proven, well-understood security model.

**Conclusion:** You cannot fully eliminate SSH for ongoing management without building or adopting a coordination service. But you *can* minimize exposure and separate concerns.

### Recommended approach: age-encrypted setup key + cloud-init

Use SSH, but make it boring and locked down:

**1. Setup-only SSH key, encrypted with age in the repo:**

```
porthole init:
  - Generates WireGuard keypairs (already does this)
  - Generates SSH ed25519 keypair with passphrase
  - Encrypts private key with age → setup-key.sops.yaml
  - Public key stored unencrypted in network.sops.yaml
```

This key is:
- **Single-purpose** — only authorized for provisioning commands, not guacamole
- **Encrypted at rest** in the repo (sops/age, same infra you already have)
- **Passphrase-protected** as a second factor
- **Rotatable** independently of any other credential
- **Revocable** — remove from hub authorized_keys to lock out

**2. Hub provisioning via Terraform + cloud-init:**

```yaml
#cloud-config
wireguard:
  interfaces:
    - name: wg0
      config_path: /etc/wireguard/wg0.conf
      content: |
        [Interface]
        PrivateKey: ${hub_wg_private_key}
        Address: 10.100.0.1/24
        ListenPort: 51820
        [Peer]
        PublicKey: ${first_spoke_wg_public_key}
        AllowedIPs: 10.100.0.2/32

users:
  - name: porthole
    shell: /bin/bash
    ssh_authorized_keys:
      - ${setup_ssh_public_key}
    sudo: "ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick, /bin/systemctl"

runcmd:
  - systemctl enable --now wg-quick@wg0
  # Firewall: WireGuard open, SSH restricted to WG subnet after 10 min
  - ufw allow 51820/udp
  - ufw allow from 10.100.0.0/24 to any port 22
  - ufw enable
  # Close public SSH after initial provisioning window
  - "at now + 10 minutes <<< 'ufw delete allow 22/tcp'"
```

At boot: WireGuard + SSH both up. SSH accepts only the setup key. Public SSH auto-closes after 10 minutes. After that, SSH only reachable over WireGuard.

**3. Spoke N+1 enrollment:**

```
From provisioning workstation (already on WG network):
  porthole add spoke-name
  porthole sync          → SSH to hub@10.100.0.1 via WG tunnel
                            using setup key (decrypted from sops)
  porthole gen-peer-scripts spoke-name → hand config to new spoke

From provisioning workstation (NOT yet on WG, e.g. fresh install):
  porthole sync          → SSH to hub@public-ip:22
                            using setup key (decrypted from sops)
                            public SSH must be re-opened temporarily:
                            porthole hub-ssh-open (adds ufw allow 22)
```

**4. Separation from guacamole:**

The setup SSH key governs `porthole sync` access only. It authenticates as a `porthole` user with limited sudo (wg, wg-quick, systemctl). Guacamole credentials (RDP/VNC passwords, per-peer SSH keys) are entirely separate, managed in `network.sops.yaml` under different fields, and never touch the setup key.

### Security model summary

| Layer | Credential | Storage | Access |
|-------|-----------|---------|--------|
| WireGuard tunnel | Hub + peer keypairs | network.sops.yaml (age-encrypted) | Kernel WireGuard |
| Hub provisioning SSH | Setup ed25519 key + passphrase | setup-key.sops.yaml (age-encrypted) | `porthole` user, limited sudo |
| Guacamole access | Per-peer passwords/keys | network.sops.yaml (age-encrypted) | Guacamole server only |

Three separate credential domains. Compromising one doesn't give access to the others.

## WireGuard vs Nebula — side-by-side comparison

Nebula (MIT, slackhq/nebula, 17.1k stars) is a certificate-based overlay network built by Slack, running on 50,000+ production hosts. It's a genuine alternative to WireGuard, not a wrapper around it. This section evaluates both against VISION-001 requirements and guiding principles.

### Architecture comparison

| Aspect | WireGuard (current) | Nebula |
|--------|-------------------|--------|
| **Protocol** | WireGuard (Noise protocol, ChaCha20-Poly1305) | Custom (Noise framework, AES-256-GCM default) |
| **Execution** | Kernel module (Linux), userspace (macOS/Windows) | Userspace on all platforms |
| **Topology** | Point-to-point tunnels; hub-and-spoke via config | Mesh by default; lighthouse for discovery |
| **NAT traversal** | Relies on hub relay (all traffic through VPS) | Built-in UDP hole punching via lighthouse; direct peer-to-peer when possible, relay as fallback |
| **Identity model** | Pre-shared public keys per peer | Certificate Authority signs host certs with name, IP, groups |
| **Peer enrollment** | Add public key + AllowedIPs to every peer that needs to reach it | Sign a cert offline with CA key; distribute cert + config to new node; lighthouse discovers automatically |
| **Hub config on new peer** | Must update hub's WG config and reload (the spoke N+1 problem) | No hub/lighthouse config change needed — lighthouse learns new peers from their signed certs |
| **DNS** | External (CoreDNS on hub, separate config) | External (same — Nebula doesn't provide DNS) |
| **Firewall/ACL** | External (ufw/nftables on hub) | Built-in: group-based firewall rules in config YAML |
| **Performance** | Kernel-level on Linux — near line-rate | Userspace — measurably slower, but adequate for remote desktop at ~10 peers |
| **Maturity** | In Linux kernel since 5.6 (2020); ubiquitous | Production at Slack since 2019; stable but smaller ecosystem |

### Evaluation against VISION-001 requirements

| # | Requirement | WireGuard | Nebula | Notes |
|---|------------|-----------|--------|-------|
| R1 | Any node reaches any other | Yes (hub relay) | Yes (direct mesh + lighthouse relay) | Nebula can do direct peer-to-peer, reducing latency. WireGuard routes everything through VPS |
| R2 | SSH via stable hostnames | Yes (CoreDNS on hub) | Requires same CoreDNS setup | Neither provides DNS natively for `.wg` names |
| R3 | Remote desktop via Guacamole | Yes (Guacamole on hub) | Yes (Guacamole on hub/lighthouse) | Both need the same Guacamole setup — orthogonal to tunnel layer |
| R4 | NAT traversal without port forwarding | Yes (hub relay always works) | Yes (hole punching + lighthouse relay) | WireGuard is simpler (always relay). Nebula tries direct first, falls back to relay |
| R5 | Network isolation | Via hub nftables rules | Built-in group-based firewall rules | Nebula's firewall is more elegant — groups in certs, rules in config |
| R6 | Family passive after setup | Yes | Yes | Both run as background daemons after enrollment |
| R7 | Automated provisioning (TUI) | Yes (existing `porthole` CLI + TUI) | Would require rewriting enrollment flow | Significant rework — new cert generation, config templates, lighthouse setup |
| R8 | Low maintenance ~10 machines | SSH-based sync to update hub peer list | Cert signing offline, no hub update needed | **Nebula wins here** — spoke N+1 is dramatically simpler |
| R9 | Reasonable cost ($0–20/mo) | Same VPS for hub | Same VPS for lighthouse | Cost-neutral — lighthouse is lighter than WG hub if anything |
| R10 | Silent background operation | systemd/launchd/Windows service | systemd/launchd/`nebula.exe service install` | Both have native service management on all three platforms |

### Evaluation against guiding principles

| # | Principle | WireGuard | Nebula |
|---|-----------|-----------|--------|
| 1 | Compose, don't build | WireGuard + CoreDNS + nftables + Terraform + Ansible — all standard, composable | Nebula replaces WireGuard + partially replaces nftables. Still needs CoreDNS, Terraform. Fewer moving parts |
| 2 | Family-friendly | Invisible after enrollment | Invisible after enrollment |
| 3 | Cross-platform | Linux (kernel), macOS (userspace), Windows (userspace) | Linux/macOS/Windows all userspace. Also iOS and Android |
| 4 | Vendor resilience | WireGuard is in the Linux kernel — it's not going anywhere | MIT license, Slack-backed, 17k stars. Defined Networking offers commercial management but the OSS tool is standalone. Risk: smaller community than WireGuard |
| 5 | Role-appropriate access | Config per node | Certificate groups — `server` group gets SSH only, `workstation` group gets SSH + RDP. More natural than per-node config |
| 6 | Hub as cattle | All state in `network.sops.yaml` — rebuild hub from repo | CA key + lighthouse config in repo — rebuild lighthouse from repo. Peers don't need reconfiguration when lighthouse rebuilds (just needs same cert + IP) |

### The spoke N+1 problem — where Nebula shines

This is the critical differentiator:

**WireGuard:** Adding a new peer requires updating the hub's `wg0.conf` with the new peer's public key and AllowedIPs, then reloading. This means SSH access to the hub — either over the WireGuard tunnel (requires an existing peer) or over the public internet (security exposure). ADR-007's age-encrypted setup key + cloud-init approach mitigates this but doesn't eliminate it.

**Nebula:** Adding a new peer is entirely offline:
1. `nebula-cert sign -name "new-spoke" -ip "10.100.0.5/24" -groups "workstation"` — runs on the operator's workstation using the CA key (stored encrypted in repo)
2. Copy the signed cert + nebula config to the new node
3. Start nebula on the new node — it contacts the lighthouse, which learns about it automatically
4. **No lighthouse/hub config change. No SSH to anything. No coordination server.**

The CA private key never leaves the operator's workstation (encrypted in the repo with age). The lighthouse only needs the CA certificate (public) to validate peers. This is fundamentally simpler than any WireGuard-based spoke N+1 solution.

### Trade-offs of choosing Nebula

1. **Performance.** Nebula is userspace-only on all platforms, including Linux. WireGuard's kernel module on Linux gives near-line-rate throughput. At ~10 peers doing remote desktop through a VPS, this is unlikely to matter — the VPS uplink is the bottleneck, not tunnel encryption.

2. **Ecosystem size.** WireGuard has massively broader adoption, documentation, and tooling. Every VPS provider has WireGuard guides. Nebula's community is healthy but smaller. However, Nebula's docs are good and the Arch Wiki has a thorough page.

3. **Lighthouse is still infrastructure.** The lighthouse must have a stable public IP, just like the WireGuard hub. The VPS doesn't go away — it just runs `nebula` instead of `wg`. (Though the lighthouse is lighter since peers connect directly when possible, reducing relay load.)

4. **Guacamole still needs a fixed host.** Remote desktop gateway doesn't change — Guacamole runs on the VPS regardless. The tunnel layer underneath is orthogonal.

5. **Existing code needs adaptation.** The `porthole` CLI, Terraform modules, and cloud-init templates currently assume WireGuard. These need to be rewritten for Nebula. Since nothing is deployed, this is greenfield work rather than migration — but it is still work.

### Hybrid consideration

Could we use both? No — they solve the same layer (encrypted overlay tunnel) and would create unnecessary complexity. Pick one.

### Assessment

| Factor | Winner |
|--------|--------|
| Spoke N+1 enrollment | **Nebula** (offline cert signing, no hub update) |
| Performance | **WireGuard** (kernel module on Linux) |
| Ecosystem & documentation | **WireGuard** (massively broader) |
| Built-in firewall/ACLs | **Nebula** (group-based, in config) |
| NAT traversal | **Nebula** (direct peer-to-peer when possible) |
| Cross-platform consistency | **Nebula** (userspace everywhere) |
| Vendor resilience | **Tie** (both MIT/GPL, both well-established) |
| Credential model simplicity | **Nebula** (CA key only — no SSH setup key needed) |
| Composability | **WireGuard** (more standard, more tooling) |
| Switching cost (pre-deployment) | **Low** (nothing deployed — greenfield adaptation) |

**Nebula is the better architecture for this use case.** The certificate model elegantly solves spoke N+1, the group-based firewall is a natural fit for role-appropriate access, the credential model is simpler, and the performance difference is irrelevant at this scale. Since nothing is deployed yet, switching now avoids building infrastructure around WireGuard's spoke N+1 limitations only to work around them later.

## Recommendation

**Go with Nebula.** Nothing is deployed yet — switching tunnel layers now costs nothing. Switching later costs a rewrite.

Rationale:
1. **No sunk cost.** The provisioning CLI and Terraform modules exist in code but nothing is running in production. Adapting them to Nebula is a greenfield change, not a migration.
2. **Spoke N+1 is solved at the architecture level.** Offline cert signing eliminates the need for SSH to the hub when enrolling new peers. No setup key, no temporary SSH windows, no `hub-ssh-open` / `hub-ssh-close` dance. The entire complexity of ADR-007's SSH management layer becomes unnecessary.
3. **Credential model is cleaner.** The Nebula CA key (encrypted with age in the repo) is the single credential for network enrollment. Guacamole credentials remain separate. Two domains instead of three — simpler to reason about, fewer things to rotate.
4. **Group-based firewall is a natural fit.** VISION-001 principle 5 (role-appropriate access) maps directly to Nebula certificate groups: `server` gets SSH only, `workstation` gets SSH + RDP. No per-node nftables rules to maintain.
5. **Direct peer-to-peer when possible.** WireGuard routes all traffic through the VPS relay. Nebula tries direct connections first and falls back to relay. For remote desktop between two machines on the same LAN (or between two residential NATs that can hole-punch), this means lower latency without any configuration.
6. **Cross-platform consistency.** Nebula is userspace on all platforms — same binary, same behavior on Linux, macOS, and Windows. WireGuard's kernel module on Linux vs userspace elsewhere creates behavioral differences.
7. **Performance is adequate.** Userspace Nebula is slower than kernel WireGuard on Linux, but at ~10 peers doing remote desktop through a VPS, the bottleneck is the VPS uplink, not the tunnel encryption.

### What changes

| Component | WireGuard approach | Nebula approach |
|-----------|-------------------|-----------------|
| Tunnel layer | `wg-quick` / kernel module | `nebula` binary (userspace) |
| Hub/relay | WireGuard hub on VPS | Nebula lighthouse on VPS (lighter — peers connect directly when possible) |
| Peer enrollment | Generate WG keypair → add to hub config → SSH to hub to reload → distribute config | Sign cert with CA key → distribute cert + config to new node → done |
| Credential storage | `network.sops.yaml` (WG keys) + `setup-key.sops.yaml` (SSH key) | `network.sops.yaml` (CA key + peer certs) — no SSH key needed |
| Firewall | nftables/ufw on hub | Nebula firewall rules in config YAML (group-based) |
| DNS | CoreDNS on hub (unchanged) | CoreDNS on hub (unchanged) |
| Remote desktop | Guacamole on hub (unchanged) | Guacamole on hub (unchanged) |
| Cloud-init | Bootstrap WireGuard + SSH + ufw | Bootstrap Nebula lighthouse (simpler — no SSH/ufw dance) |
| ADR-007 | Needed (age-encrypted SSH key for spoke N+1 management) | **Not needed** — spoke N+1 is solved by offline cert signing |

### What stays the same

- SOPS/age for secret encryption in the repo
- Terraform for VPS provisioning
- Cloud-init for first-boot configuration
- CoreDNS for `.wg` hostname resolution
- Guacamole for remote desktop gateway
- `porthole` CLI for operator workflow
- Textual TUI for node enrollment
- Hub-as-cattle principle (rebuild from repo state)

### ADR-007 disposition

ADR-007 (age-encrypted setup key + cloud-init WireGuard bootstrap) should be **superseded** if Nebula is adopted. The three-credential separation model it proposes becomes unnecessary — Nebula's certificate model provides cleaner credential separation natively. A new ADR should document the Nebula adoption decision.

### Implementation outline

| Change | Where |
|--------|-------|
| Generate setup SSH keypair in `porthole init` | `src/porthole/commands/init.py` |
| Encrypt + store setup key as `setup-key.sops.yaml` | `src/porthole/commands/init.py` |
| Store setup SSH public key in `network.sops.yaml` | `src/porthole/models.py` |
| Template cloud-init with WG config + SSH pubkey | `terraform/modules/hub/cloud-init.yaml.tpl` |
| Use setup key in `porthole sync` for SSH auth | `src/porthole/commands/sync.py` |
| TUI: remove SSH assumption, add hub provisioning flow | `src/porthole_setup/screens/hub_spinup.py` |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Active | 2026-03-07 | — | Initial research — cloud-init + alternatives |
| Active | 2026-03-07 | — | Updated: spoke N+1 problem, age-encrypted setup key recommendation |
| Active | 2026-03-07 | — | Expanded: WireGuard vs Nebula side-by-side comparison against VISION-001 |
