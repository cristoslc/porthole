# Product Landscape: Remote Access for a Personal Fleet

**Supporting doc for:** [VISION-001](./(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)
**Last updated:** 2026-02-28
**Pricing verified:** 2026-02-28 (via vendor websites and reseller listings)
**Research sources:** [SPIKE-001](../../../research/Complete/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions/(SPIKE-001)-Remote-Desktop-and-Mesh-Networking-Solutions.md), [SPIKE-002](../../../research/Complete/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation/(SPIKE-002)-Commercial-Remote-Desktop-Solution-Evaluation.md), integrated platforms research

---

## Purpose

This document answers one question: **does a product (or product combination) already exist that meets all requirements, so we don't have to build anything?**

Every option — commercial products, free products, product combos, and the custom-build path — is scored against the same requirements from VISION-001. The custom build competes on equal footing; it has no special status.

---

## The two dimensions

The problem decomposes into two independent choices:

1. **Remote desktop tool** — which product streams the desktop?
2. **Networking bridge** — how do machines find and reach each other across NATs, and how does the operator get SSH?

Some products are **integrated** (bundle both: TeamViewer, MeshCentral). Others are **components** that pair with a separate networking layer. The strongest solutions are best-of-breed components composed together.

Three requirements are **dimension-specific** — they can be evaluated per component:
- R1 (cross-platform desktop) → desktop tool
- R2 (SSH), R3 (NAT traversal), R7 (isolation) → networking bridge

Four requirements are **combination-level** — they depend on both components together:
- R4 (family passive after setup) → how many apps to install? how smooth is setup?
- R5 (low maintenance) → how many products to keep running?
- R6 (cost) → sum of both components

---

## Dimension 1: Remote desktop

Scored on the desktop-specific requirement (R1). Quality is the key differentiator among tools that meet R1 but isn't captured in the requirements — it's subjective and requires hands-on testing.

| Tool | R1 Cross-platform | Desktop quality | Cost | Notes |
|------|:---:|---|---|-------|
| **NoMachine** | Y | Good. NX protocol — excellent compression, strong over slow links. Dated UI. | Free (1 concurrent conn). Enterprise: $44.50/machine/yr. | Linux heritage (NX = compressed X11). Self-hosted, no account needed. Install once, runs as service, auto-updates. |
| **RustDesk** | Y | Better on fast networks. Modern native client, polished UI. | Free | Open source. Direct IP mode works perfectly over mesh VPN. Install once, runs as service, auto-updates. |
| **Remotix / Acronis** | Y | Best. NEAR protocol — hardware-accelerated, lowest latency. | ~$45/yr Personal (2 clients). Professional (10+): unlisted. | Acquired by Acronis, uncertain future. Subscription-only. Install once, runs as service. |
| **Splashtop** | **P** (Linux second-class) | Good. Hardware-accelerated streaming. | $99/yr (10 machines) | WAN connections always relay through Splashtop servers. Install once, runs as service. |
| **MeshCentral** | Y (macOS has permission issues) | Adequate for support, not for sustained use. | Free | *Integrated* — bundles own networking. Agent install via invite link. |
| **TeamViewer** | Y | Good. Polished, reliable. | ~$610/yr (Business, 10+ devices) | *Integrated* — bundles own networking. Install once, runs as service. |

**Top component desktop tools: NoMachine and RustDesk.** Both free, both genuinely cross-platform, both install-once-and-forget. The choice between them is purely about desktop quality — NX protocol (excellent compression, dated UI) vs. RustDesk native client (modern UI, better on fast networks). This requires hands-on testing.

---

## Dimension 2: Networking bridge

Scored on network-specific requirements (R2, R3, R7).

| Layer | R2 SSH | R3 NAT | R7 Isolation | Cost | Compatible with | Notes |
|-------|:---:|:---:|:---:|---|---|-------|
| **Tailscale** | Y | Y | Y | Free (100 devices / 3 users) | Any desktop tool | WireGuard mesh. Tailscale SSH (no key mgmt). MagicDNS hostnames. ACL policies. Install once, runs as service. |
| **NoMachine Network** | **N** | Y | **N** | $84.50/yr (1 concurrent) | NoMachine only | Cloud machine discovery + relay for NM connections. No terminal SSH. No isolation. |
| **ZeroTier** | **N** | Y | P | Free (25 devices) | Any desktop tool | P2P mesh. No built-in SSH mgmt. Flow rules less mature than Tailscale ACLs. |
| **NetBird** | Y | Y | Y | Free (5 users) | Any desktop tool | WireGuard mesh with ACLs and DNS. Newer, smaller community. |
| **Product built-in** | Varies | Varies | **N** | Included | Specific product | TeamViewer, MeshCentral, Splashtop, Remotix each have own relay/NAT. None provide isolation. |

**Tailscale wins outright.** Free, solves SSH (R2) + NAT (R3) + isolation (R7), works with any desktop tool. NoMachine Network is strictly inferior — NM-only, no SSH, no isolation, $84.50/yr for less than Tailscale provides free. NetBird is the closest alternative but has a smaller free tier and less mature ecosystem.

---

## Combination matrix

Every valid combination scored against all VISION-001 requirements (R1-R7).

**Scoring:** Y = fully meets, P = partially meets, N = does not meet, — = not applicable.

**R4/R5 scoring note:** All component combos paired with Tailscale have the same R4 and R5 story. Each requires two apps installed on each machine (desktop tool + Tailscale). Both apps run as services and auto-update. Family members are passive after the operator completes initial setup. The operator's ongoing maintenance burden is comparable across desktop tools — none of them require fleet-wide config management for basic operation. R4: Y, R5: Y for all of them.

### Contenders (no N on R1-R6)

| Desktop | Network | R1 | R2 | R3 | R4 | R5 | R6 | R7 | Score | Key trade-off |
|---------|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---------------|
| NoMachine | Tailscale | Y | Y | Y | Y | Y | Y | Y | 7Y | NX: excellent compression, dated UI. Desktop quality on fast networks TBD. |
| RustDesk | Tailscale | Y | Y | Y | Y | Y | Y | Y | 7Y | Modern native client, polished UI. Better feel on fast networks. Open source. |
| Splashtop | Tailscale | P | Y | Y | Y | Y | Y | Y | 6Y 1P | $99/yr + free Tailscale. Only gap: Linux desktop is second-class (R1). |
| Remotix/Acronis | *(integrated)* | Y | P | Y | Y | Y | P | — | 4Y 2P 1— | Best desktop performance (NEAR). SSH via tunnel only (R2). Pricing unclear for >2 clients (R6). Uncertain vendor future. |
| MeshCentral | *(integrated)* | Y | P | Y | P | Y | Y | P | 4Y 3P | Single product, free. Web SSH only (R2). MSP-grade agent tray UI may confuse family (R4). No isolation (R7). |

### Near-misses (one N, worth watching)

| Desktop | Network | Score | Gap | Notes |
|---------|---------|:---:|---|-------|
| NoMachine | NM Network | 4Y 1P 2N | R2: no terminal SSH. R7: no isolation. | Illustrates why Tailscale matters. NM Network costs $84.50/yr for less than Tailscale provides free. |
| TeamViewer | *(integrated)* | 5Y 1P 1N | R6: ~$610/yr | Best all-in-one UX. Would be the answer if cost weren't a factor. SSH via web terminal only (R2: P). |
| Splashtop | *(standalone)* | 4Y 1P 1N | R2: no SSH at all | $99/yr for 10 machines. Pair with Tailscale to fix — see contenders. |

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

### Networking is settled: Tailscale

Free, solves SSH (R2) + NAT (R3) + isolation (R7), works with any desktop tool. NoMachine Network is strictly inferior. Any component desktop tool should pair with Tailscale.

### Both top combos score 7Y

**NoMachine + Tailscale and RustDesk + Tailscale are tied on the requirements matrix.** Both free, both 7Y, both install-and-go. R1-R7 don't capture the difference between them — that difference is purely desktop quality and UX:

- **NoMachine (NX protocol):** Excellent compression, strong over slow links, dated UI, Linux heritage. Mature product (15+ years).
- **RustDesk (native client):** Modern UI, better feel on fast networks, open source. Younger project.

This can only be resolved by hands-on testing, not further analysis.

### Splashtop + Tailscale is a strong third option

At 6Y 1P ($99/yr + free Tailscale), the only gap is Linux desktop quality (R1: P). If Linux machines are primarily accessed via SSH rather than desktop, Splashtop's polished commercial product makes this a compelling option.

### Custom automation is orthogonal

Adding Ansible playbooks and an operator UI (Textual TUI, local web dashboard) is an optional enhancement to *any* combo — NoMachine or RustDesk. It improves the operator experience but trades R5 from Y to P (ongoing maintenance of automation code + UI). This is a separate decision from which desktop tool to use, and should be made after the base combo is chosen and proven.

### Integrated products fill niches

**MeshCentral:** Best single-product option — free, all-in-one — but compromises on SSH quality (R2: P), family UX (R4: P), and isolation (R7: P).

**TeamViewer:** Best all-in-one UX but at ~$610/yr, overpriced for personal use. If they launch a personal tier at $10-20/mo, adopt immediately.

**Remotix/Acronis:** Best desktop performance (NEAR protocol) but uncertain vendor future — the exact scenario motivating this exploration. Worth retaining for performance-critical sessions while the subscription is active.

---

## Detailed notes

### NoMachine (desktop)

- NX protocol — originally compressed X11 forwarding, now full cross-platform remote desktop. Linux is the heritage platform; support is genuinely first-class.
- Free for personal use. No nag screens, no commercial-use detection. Fully self-hosted — no account required.
- 1 concurrent incoming connection on free tier. Enterprise Desktop ($44.50/machine/yr) removes this limit. For a single operator, the free tier is sufficient.
- Built-in NAT traversal (independent of networking bridge): UPnP/NAT-PMP, WebRTC-style hole-punching, relay fallback, reverse SSH tunnels. Can self-host STUN/TURN. These are redundant when paired with Tailscale but mean NoMachine has fallback connectivity even if Tailscale is down.
- Desktop quality: excellent over slow links (compression heritage). On fast networks, may feel less responsive than modern native clients (RustDesk, NEAR). Subjective — needs testing.

### RustDesk (desktop)

- Open source, native client, modern UI. Better desktop quality than NX on fast networks.
- Direct IP mode: connect by IP address, no relay server needed. Perfect over a mesh VPN like Tailscale — point RustDesk at the Tailscale IP and connect.
- RustDesk Server Pro (self-hosted relay + ID server) exists but is unnecessary when Tailscale provides connectivity. Only direct IP mode is needed.
- Same install-and-forget story as NoMachine: install once, runs as service, auto-updates.

### Tailscale (networking)

- WireGuard-based mesh VPN. Free tier: 100 devices, 3 users.
- Stable IPs per device. MagicDNS hostnames (`hostname.tailnet-name.ts.net`).
- Tailscale SSH: SSH access to any device on the tailnet without managing SSH keys. Auth via Tailscale identity.
- ACL policies: restrict which devices can reach which others. Fleet machines can be isolated from existing infrastructure (VMs, Docker, NAS) on the same tailnet.
- DERP relay fallback for connections that can't establish direct WireGuard tunnels.
- Installs on Linux, macOS, Windows, iOS, Android. Runs as a service, auto-updates. Family members never interact with it after setup.

### NoMachine Network (networking)

- $8.50/mo ($84.50/yr) for Personal tier (1 concurrent connection). Business: $18.50/mo. Datacenter: $32.50/mo.
- Adds cloud-based machine discovery to NoMachine free edition — registered machine IDs so you don't need IP/DNS. Enables NoMachine-to-NoMachine connections across the internet.
- **Only works with NoMachine.** Does not provide general IP connectivity, SSH, or network isolation.
- **Redundant with Tailscale.** Tailscale provides stable IPs (MagicDNS), SSH, and isolation for free. NoMachine Network's only unique value (cloud machine discovery) is superseded by MagicDNS.

### MeshCentral (integrated)

- All-in-one: remote desktop + terminal + file management + device inventory. Self-hosted Node.js process, Docker deployment, invite links for agent install.
- SSH is browser-based only — can't `ssh hostname` from terminal without MeshCentral Router port tunneling.
- macOS agent has documented click and permission issues.
- Desktop quality: adequate for support tasks, not great for sustained use.
- No network isolation between fleet machines and other infrastructure.
- MSP-grade agent tray UI could confuse non-technical family members if they interact with it.

### Acronis Cyber Protect Connect / Remotix (integrated)

- Remotix acquired by Acronis, rebranded. Perpetual licenses discontinued; subscription-only.
- Pricing: Free (15-min sessions, 2 clients), Personal (~$45/yr, 2 clients), Professional (3 clients/user, pricing unlisted).
- NEAR protocol: hardware-accelerated, low-latency — best-in-class for interactive desktop (gaming, video, design).
- On-prem status unclear post-acquisition. Previously OVA/Docker deployment.
- SSH only via VNC/RDP tunnel, not direct terminal.
- The exact vendor-resilience risk that motivates this exploration.

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

## Recommendation (original, 2026-02-27)

> **Superseded by subsequent architecture decisions.** The recommendations below were the output of the initial landscape analysis. ADR-004 and ADR-005 changed both the networking and desktop answers. See the update section below.

The networking layer is decided: **Tailscale.**

The desktop tool is the open question: **NoMachine vs RustDesk.** Both score 7Y with Tailscale. The difference is desktop quality and UX, not requirements coverage.

**Test both.** Install NoMachine + Tailscale and RustDesk + Tailscale on 2-3 machines across platforms. Compare:

1. Desktop quality — NX vs RustDesk native on fast and slow networks
2. UI polish — NoMachine's dated interface vs RustDesk's modern client
3. Connection setup — how easy is it to point each tool at a Tailscale IP and connect?
4. Family onboarding — which is easier to install on a family member's machine?

Pick whichever feels better. If either is good enough out of the box, there's nothing to build. The optional automation layer (Ansible + operator UI) is a separate decision that can be made later, on top of whichever desktop tool wins.

---

## Update: Adopted architecture (2026-02-28)

Two architecture decisions changed both dimensions of this analysis:

### Networking: WireGuard hub-and-spoke (ADR-004), not Tailscale

[ADR-004](../../../adr/Superseded/(ADR-004)-WireGuard-Hub-and-Spoke-Relay.md) originally adopted self-hosted WireGuard hub-and-spoke via an ephemeral VPS; subsequently superseded by [ADR-008](../../../adr/Adopted/(ADR-008)-Nebula-Overlay-Network.md) which adopts Nebula's certificate-based overlay network. The decision prioritized operational sovereignty and zero SaaS dependency over Tailscale's convenience. Tailscale remains on the existing tailnet for infrastructure services but is not the networking layer for the family fleet.

This changes the scoring for Dimension 2: Tailscale is no longer the networking bridge for fleet machines. Raw WireGuard — listed as "Disqualified" above because it requires a publicly routable endpoint and manual key management — is the adopted approach, with the VPS hub providing the routable endpoint and a CLI tool (`porthole`) automating key management.

### Desktop: Guacamole gateway + native protocols (ADR-005), not NoMachine/RustDesk

[ADR-005](../../../adr/Adopted/(ADR-005)-Remote-Desktop-Access-Model.md) adopted Apache Guacamole as the remote desktop gateway, using each OS's native remote access services (RDP, VNC, SSH) as the protocol layer. No custom remote desktop agent is installed on targets.

This changes the scoring for Dimension 1: Guacamole was listed as "Disqualified" above because "gateway model requires targets reachable from gateway — no NAT traversal without VPN underneath." With WireGuard providing that VPN, the disqualifying gap is eliminated. Guacamole is the adopted desktop tool.

The "test NoMachine vs RustDesk" recommendation was superseded before testing began. SPIKE-004 found that both tools have platform-specific issues with R10 (silent background operation) — RustDesk breaks keyboard input when hiding the tray on macOS, and NoMachine can't suppress notification balloons. Guacamole sidesteps both issues: targets run only native OS services (R10 satisfied trivially).

### RustDesk returns as emergency fallback

RustDesk is pre-installed on all fleet nodes as Layer 5 emergency fallback (SPIKE-006). When WireGuard is down and all other recovery layers have failed, the operator uses RustDesk via public relay to reach the broken node and fix it. This is emergency break-glass tooling, not the primary remote desktop solution.

### Revised combination

| Desktop | Network | R1 | R2 | R3 | R4 | R5 | R6 | R7 | Notes |
|---------|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|-------|
| Guacamole | WireGuard hub-and-spoke | Y | Y | Y | Y | Y | Y | Y | Adopted (ADR-004 + ADR-005). Browser-based, no client software. Native OS protocols. Ephemeral VPS hub. |
