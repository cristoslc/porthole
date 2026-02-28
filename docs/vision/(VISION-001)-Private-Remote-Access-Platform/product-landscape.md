# Product Landscape: Remote Access for a Personal Fleet

**Supporting doc for:** [VISION-001](./(VISION-001)-Private-Remote-Access-Platform.md)
**Last updated:** 2026-02-28
**Research sources:** [SPIKE-001](../../research/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions.md), [SPIKE-002](../../research/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation.md), integrated platforms research

---

## Decision matrix

Every option — products, product combos, and the custom-build option — scored against the same requirements from VISION-001.

**Scoring:** Y = fully meets, P = partially meets (see notes), N = does not meet, — = not applicable.

### Viable options

Options that don't have an N on any requirement (R1-R6). Ranked by how many requirements they fully meet.

| Option | R1 Desktop | R2 SSH | R3 NAT | R4 Family | R5 Maintenance | R6 Cost | R7 Isolation | Score | Notes |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|-------|
| **NoMachine + Tailscale** | Y | Y | Y | Y | Y | Y | Y | 7/7 | Both free. NoMachine free tier = 1 incoming connection (fine for 1 operator). Tailscale ACLs for isolation. Dated UI. No fleet mgmt without NoMachine Enterprise ($445/yr). |
| **RustDesk + Tailscale** *(this project)* | Y | Y | Y | P | P | Y | Y | 5Y 2P | RustDesk direct IP over Tailscale. Family: requires RustDesk + Tailscale install (2 apps). Maintenance: need Ansible or equivalent to manage config across 10 machines. |
| **MeshCentral** | Y | P | Y | P | Y | Y | P | 4Y 3P | Free, self-hosted, all-in-one. SSH is web-console only (not direct terminal). Family: agent install is easy but web UI is MSP-grade. Isolation: no built-in network segmentation. |
| **Splashtop Pro** | P | N* | Y | Y | Y | Y | — | 4Y 1P 1N | $99/yr, up to 10 machines. Linux support is second-class. No SSH (would need separate solution). *Could pair with Tailscale for SSH → see combo below. |
| **Splashtop Pro + Tailscale** | P | Y | Y | P | P | Y | Y | 4Y 3P | $99/yr + free Tailscale. Fixes SSH gap. Linux remote desktop still second-class. Two products to maintain + Tailscale for family = 2 installs. |
| **TeamViewer Business** | Y | P | Y | Y | Y | N | — | 5Y 1P 1N | ~$610/yr — too expensive for personal use. Otherwise excellent: just works, great NAT, good fleet management. SSH via web terminal only. |
| **Remotix On-Prem** | Y | P | Y | Y | P | P | — | 3Y 3P | $200/yr. NEAR protocol is best-in-class for performance. Acronis acquisition risk. SSH only via VNC/RDP tunnel. On-prem adds maintenance. |

### Disqualified options

Options with a hard N on a non-negotiable requirement.

| Option | Disqualifying gap | What it does well |
|--------|-------------------|-------------------|
| **Parsec** | R1: Linux cannot be a host | Best-in-class latency for gaming/video |
| **Screens 5** | R1: macOS/iOS client only | Beautiful Apple-native experience, $25/yr |
| **TeamViewer Free** | R4/R5: aggressive commercial-use detection, session limits, nag screens | Great NAT traversal when it works |
| **AnyDesk** | R6: on-prem pricing opaque + 2024 security breach + license model in flux | Decent cross-platform, lightweight client |
| **Chrome Remote Desktop** | R1/R5: limited Linux support, no fleet management, feels abandoned | Free, simple, WebRTC NAT traversal |
| **ConnectWise ScreenConnect** | R6: $540-660/yr, MSP-oriented | Excellent scripting/automation, unlimited agents |
| **BeyondTrust** | R6: $2,000+/yr enterprise pricing | Enterprise-grade security and compliance |
| **Royal TSX** | R3: no NAT traversal, no agents (connection manager only) | Multi-protocol client, good credential mgmt |
| **DWService** | R3: cloud-only, no self-hosted server option | Browser-based, easy agent install |
| **HopToDesk** | No advantage over RustDesk; community trust concerns | — |
| **Tactical RMM** | R5: 6-service deployment stack, overkill for 10 machines | Full RMM if you need monitoring/alerting |
| **Teleport** | R1: no Linux/macOS remote desktop (SSH only) | Excellent zero-trust SSH |
| **Apache Guacamole** | R3: no NAT traversal (gateway model, needs VPN underneath) | Good browser-based VNC/RDP/SSH gateway |
| **Nebula** | R4: certificate management, impractical for family | Fully self-hosted mesh, MIT license |
| **WireGuard (raw)** | R3/R4: no NAT traversal, manual key management | In-kernel, battle-tested, fast |
| **Firezone** | R5: self-hosting explicitly unsupported | WireGuard + SSO + access policies |

### Analysis

**NoMachine + Tailscale is the strongest off-the-shelf option.** Both free, covers all 7 requirements, no custom code needed. The trade-offs are NoMachine's dated UI and 1-connection limit (fine for a single operator, but no concurrent sessions). If NoMachine's UX is tolerable, this is the answer today — no building required.

**MeshCentral is the best single product** but has three "partial" gaps: web-only SSH (no direct terminal access), MSP-grade UI for family onboarding, and no network isolation. For someone who can live with browser-based SSH and doesn't need network segmentation, MeshCentral alone might be enough.

**The custom build (RustDesk + Tailscale + automation) scores well but isn't clearly better than NoMachine + Tailscale.** The advantage is RustDesk's superior remote desktop quality and the opportunity to build a polished operator UI. The disadvantage is maintenance overhead — you're committing to managing Ansible playbooks and a TUI/dashboard indefinitely.

**TeamViewer is the obvious answer if cost weren't a factor.** At $610/yr it's overpriced for personal use, but it's the product that most completely solves the problem with zero self-management. Worth watching for pricing changes or a personal-fleet tier.

---

## Detailed notes on viable options

### NoMachine + Tailscale (top contender)

- **NoMachine** provides remote desktop (NX protocol, Linux-first heritage, free for personal use) with multiple NAT traversal strategies (UPnP, hole-punching, relay, reverse SSH).
- **Tailscale** provides mesh VPN (WireGuard-based, free tier: 100 devices/3 users), stable IPs, MagicDNS hostnames, Tailscale SSH, and ACL-based network isolation.
- Together: NoMachine handles remote desktop, Tailscale handles SSH + networking + isolation. Both install on all three platforms. Family members install two apps once.
- **Gap:** NoMachine free tier is limited to 1 incoming connection. Enterprise ($44.50/machine/yr = ~$445/yr for 10 machines) removes this but gets expensive. For a single operator this limit rarely matters.
- **Gap:** No unified fleet management — Tailscale has its admin console, NoMachine has per-machine config. No single dashboard.

### RustDesk + Tailscale (this project)

- Same architecture as above but RustDesk instead of NoMachine. RustDesk's remote desktop quality is better (native client vs. NX protocol in 2026), and its direct IP mode over Tailscale eliminates all relay infrastructure.
- The "project" part is the glue: Ansible playbooks for provisioning, and a polished operator UI (Textual TUI or local web dashboard) for enrollment and fleet state.
- **Advantage over NoMachine + Tailscale:** Better remote desktop UX. Opportunity for a delightful operator experience.
- **Disadvantage:** You're maintaining custom automation and a TUI/dashboard. NoMachine + Tailscale is install-and-go.

### MeshCentral (single product)

- Does remote desktop + terminal + file management + device inventory in one self-hosted Node.js process. Docker deployment, invite links for agents.
- **Gap:** SSH is browser-based only. Can't `ssh hostname` from your terminal without MeshCentral Router port tunneling.
- **Gap:** macOS agent has documented click and permission issues.
- **Gap:** Remote desktop quality is noticeably below RustDesk/NoMachine.
- **Gap:** No network isolation between fleet machines and other infrastructure.
- **Strength:** Single product, free, covers 90% of the use case. If the gaps are tolerable, stop here.

---

## What to watch

| Trigger | Impact |
|---------|--------|
| TeamViewer launches a personal-fleet tier ($10-20/mo) | Likely the best option — adopt and stop |
| MeshCentral adds WireGuard mesh or direct terminal SSH | Single-product answer — adopt and stop |
| NetBird adds built-in remote desktop | Single-product answer — evaluate and likely adopt |
| NoMachine improves fleet management in free tier | NoMachine + Tailscale becomes strictly dominant |
| RustDesk Server Pro drops below $5/mo and adds SSH | RustDesk becomes a single-product answer |
| Remotix stabilizes post-Acronis with reasonable pricing | Return to current tool |

---

## Recommendation

**Try NoMachine + Tailscale first.** It's the lowest-effort option that covers all requirements. Install both on a few machines, test remote desktop quality, test family onboarding flow, test SSH via Tailscale. If it works well enough, there's nothing to build.

If NoMachine's remote desktop quality or UX isn't good enough, **then** the custom build (RustDesk + Tailscale + operator UI) is justified — and the incremental cost is clear: you're trading NoMachine's install-and-go simplicity for better remote desktop and a custom operator experience.
