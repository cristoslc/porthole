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

## The two dimensions

The problem decomposes into two independent choices:

1. **Remote desktop tool** — which product provides the desktop streaming experience?
2. **Networking bridge** — how do machines find and reach each other across NATs, and how does the operator get SSH access?

Some products are **integrated** — they bundle both dimensions (TeamViewer, MeshCentral). Others are **components** that pair with a separate networking layer. The strongest solutions tend to be best-of-breed components composed together.

---

## Dimension 1: Remote desktop

Scored on desktop-specific criteria only. Networking is evaluated separately.

| Tool | R1 Cross-platform | Desktop quality | Family UX | Cost | Notes |
|------|:---:|---|:---:|---|-------|
| **NoMachine** | Y | Good. NX protocol — excellent compression, strong over slow links. Dated UI. | Y | Free (1 concurrent conn) | Linux heritage (NX = compressed X11). Self-hosted, no account needed. Enterprise: $44.50/machine/yr removes connection limit. |
| **RustDesk** | Y | Better on fast networks. Modern native client. | Y | Free | Open source. Direct IP mode (no relay needed with mesh VPN). Needs config management across fleet. |
| **Remotix / Acronis** | Y | Best. NEAR protocol — hardware-accelerated, lowest latency. | Y | ~$45/yr Personal (2 clients) | Best-in-class performance. Acquired by Acronis, uncertain future. Subscription-only. |
| **Splashtop** | P (Linux second-class) | Good. Hardware-accelerated streaming. | Y | $99/yr (10 machines) | Best price-to-value. WAN connections always relay through Splashtop servers. |
| **MeshCentral** | Y (macOS issues) | Adequate. Functional for support, not for sustained use. | P (MSP-grade UI) | Free | *Integrated* — bundles own networking. See combined scoring below. |
| **TeamViewer** | Y | Good. Polished, reliable. | Y | ~$610/yr (Business, 10+ devices) | *Integrated* — bundles own networking. See combined scoring below. |

**For component pairing, the top desktop contenders are NoMachine and RustDesk** — both free, both genuinely cross-platform, both good-to-excellent desktop quality. The choice between them is the central open question. Remotix/NEAR is performance-superior but vendor-risky; Splashtop is affordable but Linux is second-class.

---

## Dimension 2: Networking bridge

Scored on network-specific criteria only. Determines SSH access, NAT traversal, and isolation.

| Layer | R2 SSH | R3 NAT traversal | R7 Isolation | Family UX | Cost | Compatible with |
|-------|:---:|:---:|:---:|:---:|---|---|
| **Tailscale** | Y — Tailscale SSH, MagicDNS, stable IPs | Y — WireGuard mesh, DERP relay fallback | Y — ACL policies | Y — install once | Free (100 devices / 3 users) | Any desktop tool |
| **NoMachine Network** | N — NM connections only, no terminal SSH | Y — cloud machine discovery + relay | N — no segmentation | Y — built into NM client | $84.50/yr (1 concurrent conn) | NoMachine only |
| **ZeroTier** | N — no built-in SSH mgmt | Y — P2P mesh | P — flow rules, less mature than Tailscale ACLs | P — more manual config | Free (25 devices) | Any desktop tool |
| **NetBird** | Y — WireGuard, DNS | Y — WireGuard mesh | Y — ACL policies | P — newer, less polished | Free (5 users) | Any desktop tool |
| **Product built-in** | Varies | Varies | N | Y — nothing extra | Included | Specific product only |

**Tailscale is the clear winner.** Free, solves SSH + NAT + isolation, works with any desktop tool, single install for family members. The only competitor in the same tier is NetBird (less mature, smaller free tier).

**NoMachine Network is redundant when Tailscale is present.** It only works with NoMachine, doesn't provide SSH or isolation, and costs $84.50/yr for capabilities Tailscale provides for free. Its sole advantage — cloud-based machine discovery without IP addresses — is superseded by Tailscale's MagicDNS.

---

## Combination matrix

Each valid combination scored against all VISION-001 requirements (R1-R7).

**Scoring:** Y = fully meets, P = partially meets, N = does not meet, — = not applicable.

### Contenders (no N on R1-R6)

| Desktop | Network | R1 | R2 | R3 | R4 | R5 | R6 | R7 | Score | Key trade-off |
|---------|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---------------|
| NoMachine | Tailscale | Y | Y | Y | Y | Y | Y | Y | 7Y | Dated desktop UI. NX quality needs hands-on testing vs modern alternatives. |
| RustDesk | Tailscale | Y | Y | Y | P | P | Y | Y | 5Y 2P | Better desktop UX. But: 2 apps for family (R4), Ansible + operator UI maintenance (R5). |
| MeshCentral | *(integrated)* | Y | P | Y | P | Y | Y | P | 4Y 3P | Single product, free. Web-only SSH (R2). MSP UI for family (R4). No isolation (R7). |
| Splashtop | Tailscale | P | Y | Y | P | P | Y | Y | 4Y 3P | $99/yr + free TS. Linux desktop second-class (R1). 2 apps for family (R4). 2 products to maintain (R5). |
| Remotix/Acronis | *(integrated)* | Y | P | Y | Y | P | P | — | 3Y 3P 1— | Best desktop performance (NEAR). Uncertain vendor future. Subscription-only, pricing opaque for >2 clients. |

### Near-misses (one N, worth watching)

| Desktop | Network | Score | Gap | Notes |
|---------|---------|:---:|---|-------|
| NoMachine | NoMachine Network | 4Y 1P 2N | R2: no terminal SSH. R7: no isolation. | Illustrates why Tailscale is needed — NM Network only solves NM connectivity, costs $84.50/yr, provides less than Tailscale does for free. |
| TeamViewer | *(integrated)* | 5Y 1P 1N | R6: ~$610/yr | Best all-in-one if cost weren't a factor. Best NAT traversal, great fleet management, just works. SSH via web terminal only. |
| Splashtop | *(standalone)* | 4Y 1P 1N | R2: no SSH | $99/yr for 10 machines. Pair with Tailscale to fix (see contenders above). Linux desktop second-class. |

### Disqualified

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
| **Royal TSX** | R3: no NAT traversal, no agents — connection manager only | Multi-protocol client (RDP/VNC/SSH), excellent credential management. |
| **DWService** | R3: cloud-only, no self-hosted server option | Browser-based, easy agent install. |
| **HopToDesk** | No advantage over RustDesk; smaller community, trust concerns | — |
| **Tactical RMM** | R5: 6-service deployment stack, overkill for 10 machines | Full RMM with monitoring/alerting/patching. |
| **Teleport** | R1: no remote desktop for any platform (SSH/kubectl/database only) | Excellent zero-trust SSH with certificate auth and session recording. |
| **Apache Guacamole** | R3: gateway model requires targets reachable from gateway — no NAT traversal without VPN underneath | Good browser-based VNC/RDP/SSH gateway. Clientless (HTML5). |
| **Nebula** | R4: certificate-based mesh requires CA management, impractical for family | Fully self-hosted overlay mesh, MIT license, Slack heritage. |
| **WireGuard (raw)** | R3/R4: needs publicly-routable endpoint, manual key management per peer | In-kernel, battle-tested, lowest-overhead VPN. Foundation for Tailscale/NetBird. |
| **Firezone** | R5: self-hosted option explicitly unsupported as of 2025 | WireGuard-based with SSO + access policies. Cloud-hosted product pivoted. |

---

## Analysis

### The networking decision is settled

**Tailscale wins the networking dimension outright.** It's free, solves SSH (R2) + NAT traversal (R3) + isolation (R7), installs on all platforms, and works with any desktop tool. NoMachine Network is strictly inferior (NM-only, no SSH, no isolation, costs $84.50/yr). ZeroTier and NetBird are viable alternatives but less mature. Any component desktop tool should be paired with Tailscale.

### The desktop decision is the open question

With Tailscale as the networking layer, the real choice is between desktop tools:

**NoMachine + Tailscale (7Y)** is the zero-effort answer. Both free, nothing to build, covers all requirements on paper. The risk is that NX protocol's dated UI and desktop quality might not be good enough — this can only be determined by hands-on testing.

**RustDesk + Tailscale (5Y 2P)** has a better desktop experience but costs two P scores: family members install 2 apps (R4), and you maintain Ansible + operator UI indefinitely (R5). Only justified if NoMachine's desktop isn't good enough.

### Integrated products fill niches

**MeshCentral** is the best single-product option — free, all-in-one — but compromises on SSH quality, family UX, and isolation. Good enough if those gaps are tolerable.

**TeamViewer** is the best all-in-one UX but at ~$610/yr is overpriced for personal use. If they launch a personal tier at $10-20/mo, adopt immediately.

**Acronis Cyber Protect Connect** has the best desktop performance (NEAR protocol) but is the exact vendor-resilience scenario motivating this exploration. Not a long-term bet, but worth retaining for performance-critical sessions.

---

## Detailed notes

### NoMachine (desktop)

- NX protocol — originally compressed X11 forwarding, now a full cross-platform remote desktop system. Linux is the heritage platform; support is genuinely first-class.
- Free for personal use. No nag screens, no commercial-use detection. Fully self-hosted — no account required.
- 1 concurrent incoming connection on free tier. Enterprise Desktop ($44.50/machine/yr) removes this limit. For a single operator, the free tier is sufficient.
- NAT traversal (independent of networking bridge): UPnP/NAT-PMP, WebRTC-style hole-punching, relay fallback, reverse SSH tunnels. Can self-host STUN/TURN.
- NX quality: excellent over slow links (compression heritage). On fast networks, may feel less responsive than modern native clients (RustDesk, NEAR). Subjective — needs testing.

### NoMachine Network (networking)

- $8.50/mo ($84.50/yr) for Personal tier (1 concurrent connection). Higher tiers: Business $18.50/mo, Datacenter $32.50/mo.
- Adds cloud-based machine discovery — registered machine IDs so you don't need IP/DNS. Enables NoMachine-to-NoMachine connections across the internet without manual network config.
- **Only works with NoMachine.** Does not provide general IP connectivity, SSH, or network isolation.
- **Redundant with Tailscale.** Tailscale provides stable IPs (MagicDNS), SSH, and isolation for free. The only scenario where NoMachine Network adds value is if you want NoMachine standalone without any mesh VPN — but then you lose SSH (R2) and isolation (R7).

### RustDesk (desktop)

- Open source, native client, modern UI. Better desktop quality than NX on fast networks.
- Direct IP mode: connect by IP address, no relay server needed. Perfect over a mesh VPN like Tailscale.
- Needs config management across the fleet — RustDesk doesn't have fleet provisioning built in. This is where the custom build lives: Ansible playbooks + operator UI (Textual TUI or local web dashboard).
- RustDesk Server Pro (self-hosted relay + ID server) exists but adds complexity. With Tailscale providing connectivity, only the direct IP mode is needed.

### Tailscale (networking)

- WireGuard-based mesh VPN. Free tier: 100 devices, 3 users.
- Stable IPs per device. MagicDNS hostnames (`hostname.tailnet-name.ts.net`).
- Tailscale SSH: SSH access to any device on the tailnet without managing SSH keys. Auth via Tailscale identity.
- ACL policies: restrict which devices can reach which others. Fleet machines can be isolated from existing infrastructure (VMs, Docker, NAS) on the same tailnet.
- DERP relay fallback for connections that can't establish direct WireGuard tunnels.
- Installs on Linux, macOS, Windows, iOS, Android. One install, runs as a service, family members never interact with it after setup.

### MeshCentral (integrated)

- All-in-one: remote desktop + terminal + file management + device inventory. Self-hosted Node.js process, Docker deployment, invite links for agents.
- SSH is browser-based only — can't `ssh hostname` from terminal without MeshCentral Router port tunneling.
- macOS agent has documented click and permission issues.
- Desktop quality: adequate for support tasks, not great for sustained use.
- No network isolation between fleet machines and other infrastructure.
- Single product, free, covers ~90% of the use case.

### Acronis Cyber Protect Connect / Remotix (integrated)

- Remotix acquired by Acronis, rebranded. Perpetual licenses discontinued; subscription-only.
- Pricing: Free (15-min sessions, 2 clients), Personal (~$45/yr, 2 clients), Professional (3 clients/user, pricing unlisted).
- NEAR protocol: hardware-accelerated, low-latency — best-in-class for interactive desktop (gaming, video, design).
- On-prem status unclear post-acquisition. Previously OVA/Docker deployment.
- SSH only via VNC/RDP tunnel, not direct terminal.
- The exact vendor-resilience risk that motivates this exploration. Not a long-term answer.

---

## What to watch

| Trigger | Impact |
|---------|--------|
| TeamViewer launches a personal-fleet tier ($10-20/mo) | Likely the best option — adopt and stop |
| MeshCentral adds WireGuard mesh or direct terminal SSH | Single-product answer — adopt and stop |
| NetBird adds built-in remote desktop | Single-product answer — evaluate and likely adopt |
| NoMachine improves fleet management in free tier | NoMachine + Tailscale becomes strictly dominant |
| RustDesk Server Pro drops below $5/mo and adds SSH | RustDesk becomes a single-product answer |
| Acronis clarifies Cyber Protect Connect on-prem future and pricing | Re-evaluate — NEAR protocol is still best-in-class performance |

---

## Recommendation

The networking layer is decided: **Tailscale.** Nothing else comes close for free.

The desktop tool is the open question: **NoMachine vs RustDesk.**

**Try NoMachine + Tailscale first.** It scores 7Y, both products are free, and there's nothing to build. Install both on 2-3 machines across platforms and test:

1. Remote desktop quality — NX protocol on fast and slow networks
2. Family onboarding — how easy is it to install NoMachine + Tailscale on a family member's machine?
3. SSH via Tailscale — MagicDNS hostnames, Tailscale SSH
4. ACL isolation — fleet machines can't see existing infrastructure

If it works well enough, stop. The best outcome is discovering there's nothing to build.

If NoMachine's desktop quality or UX isn't good enough, **then** swap NoMachine for RustDesk and build the glue (Ansible provisioning + operator UI). The incremental cost is clear: you're trading NoMachine's install-and-go simplicity for better desktop UX and ongoing maintenance. That trade-off should be made with evidence from hands-on testing, not assumed upfront.
