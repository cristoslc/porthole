# Product Landscape: Remote Access for a Personal Fleet

**Supporting doc for:** [VISION-001](./(VISION-001)-Private-Remote-Access-Platform.md)
**Last updated:** 2026-02-28
**Pricing verified:** 2026-02-28 (via vendor websites and reseller listings)
**Research sources:** [SPIKE-001](../../research/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions.md), [SPIKE-002](../../research/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation.md), integrated platforms research

---

## Purpose

This document answers one question: **does a product (or product combination) already exist that meets all requirements, so we don't have to build anything?**

Every option — commercial products, free products, product combos, and the custom-build path — is scored against the same requirements from VISION-001. The custom build competes on equal footing; it has no special status.

---

## Decision matrix

**Scoring:** Y = fully meets, P = partially meets (see notes), N = does not meet, — = not applicable.

### Contenders

Options with no N on any non-negotiable requirement (R1-R6). These are the options worth serious evaluation. Ranked by total Y count.

| Option | R1 Desktop | R2 SSH | R3 NAT | R4 Family | R5 Maintenance | R6 Cost | R7 Isolation | Score | Notes |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|-------|
| **NoMachine + Tailscale** | Y | Y | Y | Y | Y | Y | Y | 7Y | Both free. NoMachine free tier = 1 incoming connection (fine for 1 operator). Tailscale provides stable IPs, Tailscale SSH, MagicDNS, and ACL isolation. NoMachine UI is dated. No unified fleet dashboard. |
| **RustDesk + Tailscale** *(custom build)* | Y | Y | Y | P | P | Y | Y | 5Y 2P | RustDesk direct IP over Tailscale bypasses all relay infrastructure. Family: 2 apps to install. Maintenance: need Ansible + operator UI to manage config across 10 machines — ongoing commitment. |
| **MeshCentral** | Y | P | Y | P | Y | Y | P | 4Y 3P | Free, self-hosted, all-in-one (remote desktop + terminal + file mgmt + device inventory). SSH is web-console only, not direct terminal. Family: agent install is easy but web UI is MSP-grade. No network segmentation. |
| **Splashtop Pro + Tailscale** | P | Y | Y | P | P | Y | Y | 4Y 3P | $99/yr + free Tailscale. Fixes Splashtop's SSH gap. Linux remote desktop still second-class. Two products to maintain; family needs 2 app installs. |
| **Acronis Cyber Protect Connect** *(formerly Remotix)* | Y | P | Y | Y | P | P | — | 3Y 3P 1— | Subscription-only: Free (15-min sessions, 2 clients), Personal (~$45/yr, 2 clients), Professional (3 clients/user, pricing unlisted). NEAR protocol is best-in-class for performance. On-prem status unclear post-acquisition. SSH only via VNC/RDP tunnel. Product direction uncertain under Acronis. |

### Near-misses

Strong options with one critical gap. Worth watching — a pricing or feature change could make them contenders.

| Option | R1 Desktop | R2 SSH | R3 NAT | R4 Family | R5 Maintenance | R6 Cost | R7 Isolation | Score | Gap | Notes |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|-------|
| **TeamViewer Business** | Y | P | Y | Y | Y | **N** | — | 5Y 1P 1N | R6: ~$610/yr | Otherwise the most complete solution — best NAT traversal, great fleet management, just works. Would be the answer if cost weren't a factor. SSH via web terminal only. |
| **Splashtop Pro** *(standalone)* | P | **N** | Y | Y | Y | Y | — | 4Y 1P 1N | R2: no SSH | $99/yr for up to 10 machines — best price-to-value. But no SSH at all; pair with Tailscale to fix (see contenders). Linux desktop is second-class. |

### Disqualified options

Options with fundamental, unfixable gaps on non-negotiable requirements.

| Option | Disqualifying gap | What it does well |
|--------|-------------------|-------------------|
| **Parsec** | R1: Linux cannot be a host | Best-in-class latency for gaming/video. Free P2P tier. |
| **Screens 5** | R1: macOS/iOS client only | Beautiful Apple-native experience, $25/yr. Tailscale integration. |
| **TeamViewer Free** | R4/R5: aggressive commercial-use detection, session limits, nag screens | Great NAT traversal when it works. |
| **AnyDesk** | R6: on-prem pricing opaque + 2024 security breach (source code + signing keys) + license model in flux (user-based → connection-based) | Decent cross-platform, lightweight client. Solo tier $12.99/mo. |
| **Chrome Remote Desktop** | R1/R5: limited Linux support (Debian/Ubuntu only, X11 required), no fleet management, minimal updates | Free, simple, WebRTC NAT traversal. Good for ad-hoc use. |
| **ConnectWise ScreenConnect** | R6: $540-660/yr, MSP-oriented. Server requires Windows. | Excellent scripting/automation, unlimited agents, session recording. |
| **BeyondTrust** | R6: $2,000+/yr enterprise pricing | Enterprise-grade security and compliance (SOC 2, HIPAA). |
| **Royal TSX** | R3: no NAT traversal, no agents — it's a connection manager, not a remote access solution | Multi-protocol client (RDP/VNC/SSH), excellent credential management. |
| **DWService** | R3: cloud-only, no self-hosted server option | Browser-based, easy agent install. |
| **HopToDesk** | No advantage over RustDesk; smaller community, trust concerns | — |
| **Tactical RMM** | R5: 6-service deployment stack (MeshCentral + Saltstack + Nginx + Nats + Redis + PostgreSQL), overkill for 10 machines | Full RMM with monitoring/alerting/patching. |
| **Teleport** | R1: no remote desktop for any platform (SSH/kubectl/database only) | Excellent zero-trust SSH with certificate auth and session recording. |
| **Apache Guacamole** | R3: gateway model requires all target machines be reachable from the gateway — no NAT traversal without VPN underneath | Good browser-based VNC/RDP/SSH gateway. Clientless (HTML5). |
| **Nebula** | R4: certificate-based mesh requires CA management, impractical for non-technical family members | Fully self-hosted overlay mesh, MIT license, Slack heritage. |
| **WireGuard (raw)** | R3/R4: no built-in NAT traversal (needs a publicly-routable endpoint), manual key management per peer | In-kernel, battle-tested, lowest-overhead VPN. Foundation for Tailscale/NetBird. |
| **Firezone** | R5: self-hosted option explicitly unsupported as of 2025 | WireGuard-based with SSO + access policies. Cloud-hosted product pivoted. |

---

## Analysis

**NoMachine + Tailscale is the strongest off-the-shelf option.** Both free, covers all 7 requirements, no custom code needed. The trade-offs are NoMachine's dated UI and the 1-connection limit on the free tier (fine for a single operator — concurrent sessions aren't a requirement). If NoMachine's UX is tolerable, this is the answer. No building required.

**The custom build (RustDesk + Tailscale + automation) isn't clearly better than NoMachine + Tailscale.** The advantage is RustDesk's superior remote desktop quality on fast networks and the opportunity to build a polished operator UI. The disadvantage is real and ongoing: maintaining Ansible playbooks, a Textual TUI or dashboard, RustDesk config drift, Tailscale ACL updates. This is only worth it if NoMachine's remote desktop is genuinely not good enough after hands-on testing.

**MeshCentral is the best single product** but has three "partial" gaps: web-only SSH (no direct `ssh hostname` from terminal), MSP-grade UI (intimidating for family onboarding), and no network isolation. For someone who can live with browser-based SSH and doesn't need segmentation, MeshCentral alone might be enough.

**TeamViewer is the obvious answer if cost weren't a factor.** At ~$610/yr it's overpriced for personal use, but it's the product that most completely solves the problem with zero self-management. Worth watching for pricing changes.

**Acronis Cyber Protect Connect (formerly Remotix) is in flux.** The NEAR protocol remains best-in-class for remote desktop performance — noticeably faster than competitors for latency-sensitive interactive work. But the product's future under Acronis is uncertain: subscription-only pricing, unclear on-prem status, limited documentation, no community forums. The same vendor-resilience concern that motivates this exploration applies to Acronis Cyber Protect Connect itself. Not the long-term answer, but worth retaining as a secondary tool for performance-critical sessions while the subscription is active.

---

## Detailed notes on contenders

### NoMachine + Tailscale (top contender)

**NoMachine** provides remote desktop via the NX protocol — originally a compressed X11 forwarding technology, now a full cross-platform remote desktop system. Linux is NoMachine's heritage platform; support is genuinely first-class, unlike competitors where Linux is an afterthought. Free for personal use with no nag screens or commercial-use detection. Fully self-hosted — no account required, no mandatory cloud dependency.

NAT traversal: UPnP/NAT-PMP (auto router config), WebRTC-style hole-punching, relay fallback through NoMachine Network servers, and reverse SSH tunnels. Can self-host STUN/TURN for complete relay independence.

**Tailscale** provides WireGuard-based mesh VPN with a free tier (100 devices / 3 users), stable IPs, MagicDNS hostnames, Tailscale SSH (no key management), and ACL-based network isolation.

**Together:** NoMachine handles remote desktop. Tailscale handles SSH, networking, and isolation. Both install on all three platforms. Family members install two apps once.

**Free tier limit:** NoMachine free = 1 concurrent incoming connection per machine. Enterprise Desktop ($44.50/machine/yr = ~$445/yr for 10 machines) removes this limit. For a single operator who only connects to one machine at a time, the free tier is sufficient.

**NoMachine Network subscription** ($8.50/mo or $84.50/yr for 1 concurrent connection) adds internet-based machine discovery — cloud-registered machine IDs so you don't need IP addresses or DNS names. This would let NoMachine work standalone for NAT traversal. But Tailscale already provides stable reachability + MagicDNS + SSH + isolation for free, making the Network subscription redundant in this combination.

**No unified fleet dashboard.** Tailscale has its admin console, NoMachine has per-machine config. No single pane of glass for the whole fleet.

**NX protocol quality:** Excellent over slow links (strong compression heritage). On fast local networks, modern native-client solutions (RustDesk, Remotix NEAR) may feel more responsive. Subjective — needs hands-on testing to determine if the difference matters.

### RustDesk + Tailscale (this project, if we build)

Same architecture as above but RustDesk replaces NoMachine for remote desktop. RustDesk's native client provides better remote desktop quality than NX protocol on fast networks, and its direct IP mode over Tailscale eliminates all relay infrastructure.

The "project" part is the glue: Ansible playbooks for provisioning (Linux/macOS), a polished operator UI (Textual TUI or local web dashboard) for enrollment and fleet state, and documented manual setup for Windows.

**Advantage over NoMachine + Tailscale:** Better remote desktop UX. Opportunity for a delightful operator experience with a purpose-built dashboard.

**Disadvantage:** Ongoing maintenance commitment — Ansible playbooks, RustDesk config management, Tailscale ACL updates, operator UI feature development. NoMachine + Tailscale is install-and-go; this requires indefinite upkeep.

**Only justified if** NoMachine's remote desktop quality or UX is genuinely not good enough after hands-on testing. The decision should be made with evidence, not assumed upfront.

### MeshCentral (single product)

All-in-one: remote desktop, terminal, file management, device inventory in one self-hosted Node.js process. Docker deployment, invite links for agent install. Free and open-source.

- **Gap:** SSH is browser-based only. Can't `ssh hostname` from terminal without MeshCentral Router port tunneling.
- **Gap:** macOS agent has documented click and permission issues.
- **Gap:** Remote desktop quality is noticeably below RustDesk/NoMachine — adequate for support tasks, not great for sustained use.
- **Gap:** No network isolation between fleet machines and other infrastructure.
- **Strength:** Single product, free, covers ~90% of the use case. If the gaps are tolerable, stop here.

### Splashtop Pro + Tailscale

Splashtop Pro ($99/yr for up to 10 machines) is the best price-to-value ratio in the commercial landscape. Pairing with Tailscale addresses the SSH gap and adds network isolation.

- **Gap:** Linux remote desktop is second-class — functional but fewer features than Windows/Mac.
- **Gap:** Remote (non-LAN) desktop connections always go through Splashtop relay servers — no P2P hole-punching for WAN.
- **Gap:** Two products to maintain. Family members need both apps installed.
- **Strength:** Polished commercial product with good fleet management. Wake-on-LAN support.

### Acronis Cyber Protect Connect (formerly Remotix)

Remotix was acquired by Acronis and rebranded. Perpetual licenses discontinued; subscription-only going forward. The Remotix brand and website continue to operate in parallel with the Acronis branding.

- **Current pricing:** Free (15-min sessions, 2 clients), Personal (~$45/yr, 2 clients), Professional (3 clients/user, pricing unlisted).
- **NEAR protocol** remains best-in-class for interactive desktop performance — hardware-accelerated, low-latency, noticeably faster than competitors for gaming, video, and design work.
- **On-prem status:** Unclear post-acquisition. Previously offered full on-premise deployment via OVA/Docker.
- **SSH:** Only via VNC/RDP tunnel — no direct terminal SSH.
- **Risk:** Product direction uncertain under Acronis. Limited documentation, no community forums. This is the exact vendor-resilience scenario that motivates the exploration.

---

## What to watch

| Trigger | Impact |
|---------|--------|
| TeamViewer launches a personal-fleet tier ($10-20/mo) | Likely the best option — adopt and stop building |
| MeshCentral adds WireGuard mesh or direct terminal SSH | Single-product answer — adopt and stop |
| NetBird adds built-in remote desktop | Single-product answer — evaluate and likely adopt |
| NoMachine improves fleet management in free tier | NoMachine + Tailscale becomes strictly dominant |
| RustDesk Server Pro drops below $5/mo and adds SSH | RustDesk becomes a single-product answer |
| Acronis clarifies Cyber Protect Connect on-prem future and pricing | Re-evaluate — NEAR protocol is still best-in-class performance |

---

## Recommendation

**Try NoMachine + Tailscale first.** It scores 7/7 on the requirements matrix, both products are free, and there's nothing to build. Install both on 2-3 machines across platforms and test:

1. Remote desktop quality — NX protocol on fast networks and slow networks
2. Family onboarding flow — how easy is it to install NoMachine + Tailscale on a family member's machine?
3. SSH via Tailscale — MagicDNS hostnames, Tailscale SSH (no key management)
4. ACL isolation — fleet machines can't see existing infrastructure on the tailnet

If it works well enough, stop. The best outcome is discovering there's nothing to build.

If NoMachine's remote desktop quality or UX isn't good enough, **then** the custom build (RustDesk + Tailscale + operator UI) is justified — and the incremental cost is clear: you're trading NoMachine's install-and-go simplicity for better remote desktop and a custom operator experience. That trade-off should be made with evidence from hands-on testing, not assumed upfront.
