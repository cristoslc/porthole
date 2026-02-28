# ADR-004: WireGuard Hub-and-Spoke Relay

**Status:** Adopted
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Epic:** [(EPIC-001) Remote Fleet Management](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Replaces:** [(ADR-003) Network Layer for Remote Fleet](../../adr/Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md) (Abandoned)
**Affects:** [EPIC-002](../../epic/Proposed/(EPIC-002)-Provisioning-CLI/(EPIC-002)-Provisioning-CLI.md), [EPIC-005](../../epic/Proposed/(EPIC-005)-VPS-Bootstrap/(EPIC-005)-VPS-Bootstrap.md), [EPIC-006](../../epic/Proposed/(EPIC-006)-Internal-DNS/(EPIC-006)-Internal-DNS.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Adopted | 2026-02-28 | d69e12e | Created directly as Adopted; decision made during project merge |

---

## Context

The fleet consists of ~10 machines across three platforms (Linux, macOS, Windows) at multiple physical locations — the operator's home, family members' homes, and while traveling. The network layer must provide reliable connectivity between all nodes regardless of NAT topology.

ADR-003 evaluated five options (Tailscale ACL segmentation, ZeroTier, WireGuard hub-and-spoke, RustDesk Server Pro, Tailscale + RustDesk relay) and recommended Tailscale ACLs. That recommendation was not adopted for three reasons:

1. **SaaS dependency.** Tailscale's control plane is a third-party service. The operator cannot rebuild from scratch without Tailscale being available — device registration, key exchange, and ACL enforcement all depend on their infrastructure.
2. **No vendor resilience.** The entire reason for this project is avoiding reactive migrations when vendors change direction (Remotix → Acronis). Adopting Tailscale as the network foundation creates the same single-vendor dependency.
3. **Operational sovereignty.** The operator wants the network defined in a Git repo — every peer, every key, every route — encrypted at rest and deployable to fresh infrastructure with one command. Tailscale's model (SaaS control plane, client-side agent) doesn't support this.

## Decision

**Adopt a self-hosted WireGuard hub-and-spoke relay via a VPS.**

A single VPS runs WireGuard as a relay hub. All fleet nodes connect to the hub as spokes. Inter-node traffic routes through the hub. The network's source of truth is a SOPS/age-encrypted state file (`network.sops.yaml`) in the Git repo. A CLI tool (`wgmesh`) manages the full lifecycle: initialization, peer provisioning, peer removal, config rendering, and deployment.

### Key properties

- **Fully self-hosted.** No SaaS dependency. The VPS is a commodity — any provider, any region.
- **Repo-as-source-of-truth.** Every peer, key, IP, and DNS name is defined in the repo. Clone and rebuild in under 10 minutes.
- **WireGuard.** In-kernel, battle-tested, minimal attack surface. Native clients on Linux, macOS, and Windows.
- **Hub-and-spoke, not mesh.** All traffic routes through the VPS. This sacrifices latency (two hops instead of direct P2P) for reliability — every connection works regardless of NAT topology. No hole-punching, no STUN/TURN, no fallback logic.
- **SOPS/age encryption.** Private keys never exist in plaintext in the repo. The age private key lives only on the operator's workstation and the VPS.
- **Internal DNS.** CoreDNS on the hub serves a `.wg` zone generated from the state file. `ssh mom.wg` instead of `ssh 10.100.0.10`.

### Limitations accepted

- **All traffic relays through the VPS.** Latency is higher than a direct P2P connection. Acceptable for SSH and remote desktop at personal-fleet scale.
- **VPS is a single point of failure.** If it goes down, no inter-node connectivity. Mitigated by fast disaster recovery (clone repo, point at new VPS, one command).
- **No automatic P2P hole-punching.** Two nodes on the same LAN still route through the VPS. Acceptable tradeoff for simplicity.
- **Manual key distribution.** The operator runs `wgmesh add`, then delivers the generated config to the target machine (via SSH, USB, or walking it over). No automated config push to client nodes.

## Consequences

### Positive

- **Zero SaaS dependency.** No Tailscale, no ZeroTier, no third-party control plane.
- **Disaster recovery in minutes.** The repo contains everything needed to rebuild from scratch.
- **Full operational control.** The operator owns every component: VPS, WireGuard, CoreDNS, DNS zone, firewall rules.
- **Simple mental model.** Hub-and-spoke is straightforward. No NAT traversal edge cases, no "sometimes direct, sometimes relayed" ambiguity.
- **Cross-platform.** WireGuard has native clients on Linux, macOS, Windows, iOS, and Android.

### Negative

- **Higher latency than Tailscale.** Tailscale's DERP relay is a fallback; most connections are direct P2P via WireGuard. This architecture relays everything.
- **Ongoing VPS cost.** ~$3-6/mo for a minimal VPS (1 vCPU, 1 GB RAM). Tailscale free tier has zero infrastructure cost.
- **More operational surface.** The operator maintains WireGuard, CoreDNS, the VPS OS, and the `wgmesh` CLI. Tailscale is install-and-forget.
- **No MagicDNS.** Tailscale's MagicDNS resolves hostnames automatically. This architecture requires CoreDNS configuration (automated by `wgmesh sync`, but still operator-maintained infrastructure).

## Alternatives considered

### Tailscale ACL segmentation (ADR-003 recommendation) — Not adopted

Zero additional infrastructure, free tier sufficient, easiest family onboarding. Not adopted because it creates a SaaS dependency on Tailscale's control plane with no self-hosted fallback for device registration and key exchange. Headscale exists as a self-hosted control server but is a separate project with its own maintenance burden and compatibility risks.

The detailed evaluation of Tailscale, ZeroTier, WireGuard hub-and-spoke, RustDesk Server Pro, and Tailscale + RustDesk relay is preserved in [(ADR-003) Network Layer for Remote Fleet](../../adr/Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md).

### ZeroTier (self-hosted controller) — Not adopted

True network separation, self-hosted controller removes device limits. Not adopted because it adds a new tool and service (ZeroTier controller) with a custom protocol and smaller ecosystem than WireGuard. If going self-hosted, raw WireGuard is simpler and more widely understood.

### Tailscale (retained for existing infrastructure)

Tailscale remains on the existing tailnet for VMs, Docker containers, and infrastructure services. The WireGuard relay network is a separate, parallel network for fleet access only. The two networks do not overlap — this provides the isolation (R5) that ACL segmentation would have provided.
