# Product Landscape: Remote Access for Personal Fleets

**Supporting doc for:** [VISION-001](./\(VISION-001\)-Private-Remote-Access-Platform.md)
**Date:** 2026-02-27
**Research sources:** [SPIKE-001](../../research/\(SPIKE-001\)-Remote-Desktop-and-Mesh-Networking-Solutions/\(SPIKE-001\)-Remote-Desktop-and-Mesh-Networking-Solutions.md), [SPIKE-002](../../research/\(SPIKE-002\)-Commercial-Remote-Desktop-Solution-Evaluation/\(SPIKE-002\)-Commercial-Remote-Desktop-Solution-Evaluation.md), integrated platforms research

---

## TL;DR

**No single product does everything we need.** MeshCentral comes closest as an integrated self-hosted platform, but its remote desktop quality and lack of persistent mesh networking fall short. The current architecture — mesh VPN + RustDesk + IaC automation — remains the right approach. If a commercial product ever covers all requirements, that would be a win worth switching to.

---

## Requirements recap

| # | Requirement | Non-negotiable? |
|---|-------------|:---:|
| 1 | Remote desktop across Linux, macOS, Windows | Yes |
| 2 | SSH access via stable hostnames/IPs | Yes |
| 3 | Self-hosted or P2P — no third-party traffic | Yes |
| 4 | NAT traversal without manual port forwarding | Yes |
| 5 | Non-technical family members passive after setup | Yes |
| 6 | Low maintenance for ~10 machines | Yes |
| 7 | Automation-friendly (IaC, headless setup) | Preferred |

---

## Integrated platforms (one product to rule them all?)

These products attempt to combine fleet management, remote desktop, and terminal access.

### MeshCentral — closest to a single-product replacement

Self-hosted, Apache 2.0, browser-based remote desktop + SSH + file management in one Node.js process. Covers requirements 1-6 in a single deployment.

**What works:** Remote desktop (browser-based, all platforms), integrated SSH terminal, file transfer, device inventory, agent-based NAT traversal (reverse WebSocket tunnels), unattended access, invite links for easy agent deployment, Docker deployment.

**What doesn't:** No persistent mesh VPN (session-based access, not always-on connectivity). Remote desktop quality is noticeably worse than RustDesk's native client. macOS agent has documented click/permission issues. UI is MSP-grade — functional but not delightful. Can't SSH directly from your terminal to `hostname.mesh`; must use web console or MeshCentral Router for port tunneling.

**Verdict:** Genuinely covers 90% of the use case. The missing 10% (mesh VPN for direct SSH, remote desktop quality, macOS reliability) is exactly the gap this project fills. **Worth revisiting if the fleet grows past 20 machines** and monitoring/management features become more important.

### Tactical RMM — MeshCentral with polish, but heavier

Built on MeshCentral + Django/Vue. Adds monitoring, alerting, patch management, scripting. Designed for MSPs.

**Why not:** 6-service stack (Django, Celery, Redis, PostgreSQL, Nginx, MeshCentral) is overkill for 10 machines. Windows is the first-class platform; Linux/macOS agents require community scripts. Setup and maintenance burden is disproportionate to fleet size.

### Teleport — wrong mental model

Zero-trust access platform for infrastructure. Excellent SSH. Windows RDP via browser. No graphical remote desktop for Linux or macOS. Certificate-based auth. Designed for DevOps teams, not family tech support.

**Why not:** No Linux/macOS remote desktop. Complex identity management unsuitable for family members. Community Edition licensing moving toward commercial.

---

## Remote desktop tools (head-to-head)

### Best fit: tools that meet the privacy and cross-platform requirements

| Tool | Type | Self-hosted | Cross-platform | NAT traversal | Family-friendly | Cost |
|------|------|:-----------:|:--------------:|:-------------:|:---------------:|------|
| **RustDesk** | OSS | Yes (relay) | Lin/Mac/Win | Hole-punch + relay | Moderate | Free |
| **NoMachine** | Commercial | Yes (fully) | Lin/Mac/Win | UPnP + hole-punch + relay + reverse SSH | Moderate | Free (1 conn) |
| **Remotix** (current) | Commercial | Yes (on-prem) | Lin/Mac/Win | Via gateway | Good | $200/yr/worker |

**RustDesk** — Already selected (ADR-001). Best OSS cross-platform remote desktop. Self-hosted relay. Hole-punching + relay fallback. Direct IP mode eliminates all RustDesk infrastructure when paired with a mesh VPN. Wayland support improving but still has clipboard and login-screen gaps.

**NoMachine** — Strongest commercial alternative. Linux-first heritage (NX protocol). Free for personal use with no nag screens. Self-hosted STUN/TURN for complete data sovereignty. Multiple NAT traversal strategies. Trade-offs: dated UI, 1-incoming-connection limit on free tier, $44.50/machine/year for enterprise.

**Remotix** (current tool) — NEAR protocol performance is superior for interactive/gaming/video use. On-premise deployment gives full data sovereignty. Multi-protocol flexibility (NEAR, VNC, RDP, Apple Screen Sharing). Risks: Acronis acquisition creates product uncertainty, on-premise pricing ($200/yr) is steep for personal use.

### Disqualified or inadequate

| Tool | Why not |
|------|---------|
| **Parsec** | Linux cannot be a host machine — dealbreaker |
| **TeamViewer** | No self-hosted option; ~$610/yr for 10 machines; aggressive commercial-use detection on free tier |
| **AnyDesk** | On-prem pricing opaque; 2024 security breach; license model in transition |
| **Splashtop** | Remote connections always relay through their servers (no WAN P2P); on-prem is enterprise-priced |
| **Chrome Remote Desktop** | Google dependency; no fleet management; limited Linux support; feels abandoned |
| **ConnectWise ScreenConnect** | Self-hosted server Windows-only; $540-660/yr; MSP-oriented |
| **BeyondTrust** | Enterprise pricing ($2,000+/yr) |
| **Screens 5** | macOS client only |
| **Royal TSX** | Connection manager only — no NAT traversal, no agents, no fleet management |
| **DWService** | Cloud-only; all traffic through their relay — violates privacy requirement |
| **HopToDesk** | No advantage over upstream RustDesk; community trust concerns |

---

## Mesh / overlay networking

### Recommended stack (per ADR-003)

| Priority | Tool | Model | NAT traversal | Family onboarding | Ops burden |
|----------|------|-------|:-------------:|:-----------------:|:----------:|
| **Primary** | Tailscale | SaaS control plane | Best-in-class | Easiest (install + sign in) | Zero |
| **Fallback 1** | Headscale | Self-hosted Tailscale | Same clients | Moderate (custom URL) | Medium |
| **Fallback 2** | ZeroTier (self-hosted) | Self-hosted controller | Good | Moderate (ID + approval) | Medium |
| **Monitor** | NetBird | Fully self-hosted | Good | Good (SSO) | Medium-High |

### Not recommended

| Tool | Why not |
|------|---------|
| **Nebula** | Certificate management complexity; poor mobile/family UX; "not aimed at hobbyists" |
| **WireGuard (raw)** | No NAT traversal; manual key management; impractical for non-technical users |
| **wg-easy** | Hub-and-spoke only (not mesh); hub must be publicly reachable |
| **Firezone** | Self-hosting explicitly unsupported by maintainers |

---

## Market gaps and opportunities

### What the market gets right

- **Remote desktop quality** is a solved problem — RustDesk, NoMachine, Parsec, and Remotix all deliver good-to-excellent experiences.
- **Mesh networking** is effectively solved for consumer/prosumer use — Tailscale and its ecosystem (Headscale, NetBird) provide zero-config mesh VPNs.
- **Fleet management at scale** (100+ machines) is well-served by MeshCentral, Tactical RMM, and commercial RMM tools.

### What the market misses (our niche)

1. **Privacy-first + family-friendly is an empty quadrant.** Tools are either privacy-first but complex (raw WireGuard, Nebula) or family-friendly but cloud-dependent (TeamViewer, Chrome Remote Desktop). Nothing combines "no third-party traffic" with "non-technical family member can use it."

2. **Small-fleet sweet spot is underserved.** MSP tools (MeshCentral, Tactical RMM) assume hundreds of machines and IT professionals. Consumer tools (TeamViewer, AnyDesk) assume a single user connecting to 1-3 machines. A fleet of ~10 mixed-OS machines managed by one technical person with non-technical family members falls between these models.

3. **No integrated mesh VPN + remote desktop product exists.** Every solution is either a mesh VPN OR a remote desktop tool. MeshCentral comes closest by bundling both, but its session-based access model is not a true mesh VPN (no direct SSH from terminal, no always-on connectivity).

4. **Operator experience is universally poor.** Every option requires shell commands, config files, or enterprise web UIs. Nothing provides a polished local operator experience (TUI/dashboard) for a small self-hosted fleet.

### Could we just buy something?

**Not today.** The gap is real: no product combines self-hosted mesh networking + quality remote desktop + SSH + cross-platform + family-friendly onboarding + low maintenance at small scale. The closest candidates:

- **MeshCentral** — if you can accept browser-based remote desktop quality and no persistent mesh VPN.
- **Tailscale + RustDesk** — if you accept it's two tools, not one.
- **NoMachine + Tailscale** — similar to above but NoMachine instead of RustDesk.

If MeshCentral ever adds WireGuard mesh networking or if NetBird adds built-in remote desktop, one of them could become the single-product answer. Watch both.

---

## Decision summary

| Layer | Selected tool | Rationale |
|-------|--------------|-----------|
| Mesh networking | Tailscale (Headscale fallback) | Best NAT traversal, easiest family onboarding, zero ops (ADR-003) |
| Remote desktop | RustDesk | Best OSS cross-platform desktop, self-hosted, direct IP mode over Tailscale (ADR-001) |
| Provisioning | Ansible + operator UI (TBD) | IaC for Linux/macOS; guided manual for Windows |
| Operator experience | TBD (Textual TUI / local web) | Gap in every existing product — the differentiator for this project |
