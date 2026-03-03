# SPIKE-002: Commercial Remote Desktop Solution Evaluation

**Status:** Complete
**Author:** Claude
**Created:** 2026-02-27
**Last Updated:** 2026-02-27
**Parent:** [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-27 | 6df2003 | Research conducted and findings documented in single session |

---

## Question

Which commercial remote desktop solution best fits a personal fleet of ~10 machines across Linux, macOS, and Windows with privacy, NAT traversal, unattended access, and low-maintenance requirements?

## Gate

Pre-implementation. This spike informs the desktop tool selection and validates alternatives to RustDesk.

### Go criteria

- At least 10 commercial remote desktop solutions evaluated with current (2025-2026) data.
- Each solution assessed against: platforms, self-hosting, pricing, P2P vs relay, NAT traversal, unattended access, Linux quality, privacy, and automation.

### No-go pivot

Not applicable — this is an informational spike, not a gating decision. Findings feed into the product landscape.

## Risks addressed

- Vendor lock-in to a tool that does not meet cross-platform or privacy requirements.
- Ongoing subscription costs for a personal fleet.
- Reliance on third-party relay servers for sensitive traffic.
- Poor Linux support undermining cross-platform coverage.

## Dependencies

- None. This spike is pure research.

## Research Objective

Evaluate 11 commercial remote desktop and remote access solutions against the requirements of managing a personal fleet of approximately 10 machines spanning Linux, macOS, and Windows. The evaluation criteria are:

1. **Remote desktop + SSH access** across all machines
2. **Privacy**: ideally self-hosted or P2P, no traffic through third-party relay servers
3. **Cross-platform**: Linux, macOS, Windows all first-class
4. **NAT traversal** without manual port forwarding
5. **Non-technical family members** can use enrolled machines passively (no action required after initial setup)
6. **Low maintenance** for ~10 machines
7. **Bonus**: Automation-friendly (CLI install, config files, headless setup)

---

## Solution Evaluations

### 1. Remotix (current tool)

**Note on product status:** Remotix was acquired by Acronis and rebranded as "Acronis Cyber Protect Connect." However, the Remotix brand and website (remotix.com) continue to operate with Remotix 6, and the product appears to maintain a dual identity -- Remotix for the standalone/on-premise product and Acronis Cyber Protect Connect for the cloud-managed subscription version. Remotix perpetual licenses were discontinued; the product is now subscription-only.

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, iOS, Android, tvOS (client); Windows, macOS, Linux (host via Remotix Agent) |
| **Pricing** | Cloud: subscription (pricing not publicly listed, formerly perpetual ~$40-80). On-premise: $200/year per worker (unlimited remote machines, Agent is free) |
| **Self-hosted** | Yes -- full on-premise deployment via OVA, Docker, or manual install |
| **P2P vs Relay** | Supports both. Direct connections when possible; Remotix Cloud provides tunneling for NAT/firewall traversal |
| **NAT traversal** | Via Remotix Cloud tunneling (relay) or on-premise gateway. No built-in hole-punching |
| **Unattended access** | Yes -- via Remotix Agent installed on target machines. Trusted Users list enables passwordless access |
| **Linux support** | Good. Native agent and client. Hand-optimized per platform |
| **Privacy/data routing** | On-premise option keeps all data within your network. Cloud option routes through Remotix/Acronis relay infrastructure |
| **Protocols** | NEAR (proprietary, hardware-accelerated, low-latency), VNC, Apple Screen Sharing, RDP |
| **Automation** | Remotix Hub web interface for fleet management, monitoring, and reporting |

**Strengths:**
- NEAR protocol provides excellent performance -- users report it is noticeably faster than competitors for interactive desktop use, gaming, and video
- On-premise option gives full data sovereignty at reasonable cost
- Multi-protocol support (NEAR, VNC, RDP, Apple Screen Sharing) is unusually flexible
- Proactive monitoring catches HDD, firewall, battery, and security update issues
- Users consistently praise setup simplicity and responsiveness
- True cross-platform with native apps hand-optimized for each platform

**Weaknesses:**
- Acquisition by Acronis creates product identity confusion and licensing uncertainty
- Perpetual licenses discontinued -- subscription-only going forward
- Minimal documentation, no support forums, limited community
- Cloud Hub has organizational bugs (groups can be overwritten on app open)
- Scrolling behavior reported as inconsistent
- On-premise pricing ($200/year/worker) is expensive for a single user managing a personal fleet
- NAT traversal requires either cloud relay or on-premise gateway -- no built-in P2P hole-punching

---

### 2. TeamViewer

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, Chrome OS, iOS, Android, Raspberry Pi |
| **Pricing** | Free for personal use (limited). Remote Access: ~$24.90/mo (1 user, 3 devices). Business: ~$50.90/mo (200 managed devices). Premium: ~$112.90/mo. Corporate: ~$229.90/mo. All billed annually only |
| **Self-hosted** | No true self-hosted option. TeamViewer Tensor (enterprise) offers a dedicated connection router but the infrastructure remains TeamViewer-managed |
| **P2P vs Relay** | Hybrid. Direct P2P via UDP/TCP in ~70% of connections; remaining 30% routed through TeamViewer relay servers |
| **NAT traversal** | Built-in. Attempts direct connection first, falls back to relay seamlessly. Works behind most NATs/firewalls without configuration |
| **Unattended access** | Yes -- full unattended access with password/2FA. Install and forget |
| **Linux support** | Good. Native client and host. Supports major distributions |
| **Privacy/data routing** | RSA 4096 key exchange + AES 256-bit encryption end-to-end. TeamViewer relay servers cannot read encrypted traffic. However, ~30% of sessions do transit TeamViewer infrastructure. No option to avoid their servers entirely (except on LAN) |
| **Automation** | MSI installer, group policies, mass deployment via management console |

**Strengths:**
- Best-in-class NAT traversal -- just works everywhere
- Free personal tier exists (though increasingly restricted)
- Excellent unattended access with minimal setup
- Very polished cross-platform experience
- Mass deployment and management console for fleet operations
- Strong encryption even through relay

**Weaknesses:**
- Aggressive commercial use detection -- personal users frequently get flagged and locked out
- No self-hosted option; all traffic potentially traverses TeamViewer servers
- Expensive for commercial tiers ($50-230/mo billed annually)
- Free tier has session time limits and nag screens
- Privacy-conscious users cannot avoid TeamViewer's relay infrastructure
- Remote Access plan only manages 3 devices -- inadequate for 10-machine fleet without Business tier ($50.90/mo = $610/year)

---

### 3. AnyDesk

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, FreeBSD, iOS, Android, Chrome OS, Raspberry Pi |
| **Pricing** | Solo: $12.99/user/mo. Standard: $25.99/user/mo. Advanced: $67.99/user/mo. On-premise: custom pricing (contact sales). License model transitioning from user-based to connection-based as of October 2025 |
| **Self-hosted** | Yes -- AnyDesk On-Premises lets you host your own AnyDesk appliance server on internal network (physical or virtual hardware) |
| **P2P vs Relay** | Hybrid. Direct connections enabled by default; can be disabled to force relay through AnyDesk servers. All sessions end-to-end encrypted regardless of connection type |
| **NAT traversal** | Built-in. Automatic direct connection with relay fallback |
| **Unattended access** | Yes -- set password for unattended access, deploy and forget |
| **Linux support** | Good. Native client for major distributions. FreeBSD also supported |
| **Privacy/data routing** | TLS 1.2 encryption, RSA 2048 asymmetric key exchange. On-premise option keeps all data within your network. Cloud version routes through AnyDesk relay infrastructure when direct connection fails |
| **Automation** | MSI/PKG installers, custom namespace, centralized management console, device management in Advanced tier |

**Strengths:**
- On-premise option for full data sovereignty
- Lightweight client with fast connection establishment
- Broad platform support including FreeBSD and Raspberry Pi
- Direct connection support reduces relay dependency
- Custom branding and namespace in higher tiers
- Solo tier at $12.99/mo is relatively affordable

**Weaknesses:**
- On-premise pricing is custom/opaque -- likely expensive for personal use
- License model in transition (user-based to connection-based) creates uncertainty
- Solo tier may be insufficient for 10 machines -- unclear connection limits in new model
- On-premise requires running your own appliance server (maintenance burden)
- 2024 security breach (source code and signing keys compromised) raised trust concerns

---

### 4. Parsec

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, Android, Raspberry Pi (client). Windows, macOS (host only -- **Linux cannot be a host**) |
| **Pricing** | Free for personal use (1 monitor, basic features). Warp (individual): $8.33/mo (annual). Teams: $30/user/mo. Enterprise: $45/user/mo |
| **Self-hosted** | No. Cloud infrastructure only. Enterprise tier gets "high-performance relay servers" but these are Parsec-managed |
| **P2P vs Relay** | P2P by default for personal use (encrypted peer-to-peer). Enterprise tier adds relay servers |
| **NAT traversal** | Built-in P2P hole-punching. Generally works without configuration |
| **Unattended access** | Yes -- host app runs as a service, accessible remotely after setup |
| **Linux support** | **Client only**. Linux cannot serve as a host machine. This is a critical limitation |
| **Privacy/data routing** | P2P connections are direct and encrypted. No data transits Parsec servers for personal tier. Enterprise relay traffic goes through Parsec infrastructure |
| **Automation** | CLI installation, configuration file support, headless setup supported on client side |

**Strengths:**
- Excellent performance -- purpose-built for low-latency, high-FPS streaming (gaming heritage)
- Free tier with genuine P2P (no relay) is excellent for privacy
- Very good NAT traversal via hole-punching
- 4:4:4 color mode in Warp tier (important for design/development work)
- Good automation support with CLI and config files

**Weaknesses:**
- **Linux cannot be a host** -- disqualifying for a mixed fleet requirement
- Owned by Unity Technologies -- future uncertain given Unity's financial pressures
- No self-hosted option
- Free tier limited to single monitor
- No SSH integration -- pure remote desktop only
- Teams tier requires minimum 5 members ($150/mo minimum)

---

### 5. Splashtop

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, Chrome OS, iOS, Android |
| **Pricing** | Remote Access Solo: $60/year (1 user, limited computers). Remote Access Pro: $99/user/year (up to 10 computers). Remote Support SOS: $259/year (10 unattended). Enterprise: custom pricing |
| **Self-hosted** | Yes -- Splashtop On-Prem available for self-hosted deployment. Enterprise pricing, contact sales |
| **P2P vs Relay** | Hybrid. Automatic LAN direct connection (P2P via TCP port 6783) when both devices are local. Remote connections route through Splashtop relay servers (TLS over port 443) |
| **NAT traversal** | Built-in via relay servers. Direct connection only on same LAN |
| **Unattended access** | Yes -- Splashtop Streamer installed on target machines enables unattended access |
| **Linux support** | Supported but not first-class. Linux Streamer available for unattended access. Fewer features compared to Windows/Mac |
| **Privacy/data routing** | AES 256-bit encryption, TLS, 2FA, device authentication. Cloud version routes remote traffic through Splashtop relay servers. On-Prem option keeps everything within your infrastructure |
| **Automation** | Mass deployment tools, MSI installer, group policy support |

**Strengths:**
- Remote Access Pro at $99/year for up to 10 computers is the best price-to-value for this fleet size
- On-prem option exists for full data control
- Good performance with hardware-accelerated streaming
- Simple setup -- install Streamer on targets, connect from app
- Wake-on-LAN support

**Weaknesses:**
- Remote (non-LAN) connections always go through Splashtop relay servers -- no P2P hole-punching for WAN
- On-prem pricing is enterprise-grade (not publicly listed, likely $1000+/year)
- Linux support is functional but secondary -- fewer features than Windows/Mac
- No SSH integration in the remote desktop product
- LAN-only direct connection means privacy requires the on-prem product

---

### 6. Chrome Remote Desktop

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux (Debian/Ubuntu 64-bit), Chrome OS. Client: any device with Chrome browser |
| **Pricing** | Completely free. No tiers, no limits, no subscriptions |
| **Self-hosted** | No. Google-managed infrastructure entirely |
| **P2P vs Relay** | Hybrid. Attempts P2P first via WebRTC (Chromoting protocol). Falls back to Google/AWS relay servers. End-to-end encrypted regardless |
| **NAT traversal** | Built-in via WebRTC ICE/STUN/TURN. Generally works well behind NATs |
| **Unattended access** | Yes -- "Remote Access" mode provides always-on access with a PIN. Works on Windows, Mac, Linux (not Chrome OS) |
| **Linux support** | Functional but limited. Debian/Ubuntu 64-bit only. Requires X11 desktop environment (XFCE recommended for headless). Initial setup requires a browser with logged-in Google account |
| **Privacy/data routing** | End-to-end encrypted. Google collects anonymized session metadata (latency, duration). When direct P2P fails, traffic routes through Google/AWS servers (encrypted, but Google infrastructure is involved) |
| **Automation** | Headless Linux setup possible via CLI. No fleet management, no mass deployment tools, no centralized console |

**Strengths:**
- Completely free with no commercial-use restrictions
- WebRTC-based NAT traversal is reliable
- Simple setup for non-technical users
- Tied to Google account -- familiar authentication model
- End-to-end encryption even through relay

**Weaknesses:**
- Requires Google account -- privacy trade-off
- No centralized fleet management -- each machine managed individually
- No file transfer (drag-and-drop)
- No multi-session handling
- No SSH integration
- Limited Linux distribution support (Debian/Ubuntu only)
- No Wake-on-LAN
- Cannot wake machines from sleep
- No audit logs or administrative controls
- Google collects session metadata
- Feels like an abandoned Google product -- minimal updates, sparse documentation

---

### 7. ConnectWise ScreenConnect (formerly ConnectWise Control)

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, iOS, Android. Server: Windows only (Linux server support ended December 2021) |
| **Pricing** | One: $30/mo (annual, 1 session, 10 unattended agents). Standard: $45/mo (annual) or $59/mo (monthly), unlimited unattended agents. Premium: $55/mo (annual) or $69/mo (monthly). On-premise: contact sales |
| **Self-hosted** | Yes -- ScreenConnect On-Premise available. The server is a .NET Framework application (Windows only). Self-hosted gives full control over data routing |
| **P2P vs Relay** | Relay through ScreenConnect server (cloud or self-hosted). Bridge Connectivity feature for NAT traversal. Not P2P |
| **NAT traversal** | Built-in via relay architecture. "Bridge Connectivity" handles firewalls, NATs, and network restrictions. Self-hosted server acts as relay |
| **Unattended access** | Yes -- deploy access agents to unlimited machines (Standard+ tiers). Single installer works across unlimited devices |
| **Linux support** | Linux client/agent supported. **Linux server hosting ended December 2021** -- server must run on Windows. Linux agents for unattended access still work |
| **Privacy/data routing** | Self-hosted option means all data stays within your infrastructure. Cloud version routes through ConnectWise servers |
| **Automation** | Scripting extensions, custom installers, mass deployment, PowerShell integration, Wake-on-LAN, remote command line |

**Strengths:**
- Self-hosted option with full data sovereignty
- Unlimited unattended agents on Standard+ tiers -- ideal for fleet management
- Very capable remote management (remote command line, scripting, file transfer)
- Session recording and audit capabilities
- Extensible via plugins and scripting
- MSP-grade fleet management tools

**Weaknesses:**
- Self-hosted server requires Windows -- cannot run on Linux
- Expensive for personal use ($45-55/mo = $540-660/year)
- Designed for MSP/IT support, not personal remote access -- UX reflects this
- .NET Framework dependency limits deployment flexibility
- On-premise pricing not publicly listed (likely more expensive than cloud)
- Overkill feature set for a 10-machine personal fleet

---

### 8. BeyondTrust (formerly Bomgar)

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux, iOS, Android, Chrome OS |
| **Pricing** | Custom/enterprise pricing only. Not publicly listed. Historical data suggests $150+/year per shared license. Expect $2,000+/year minimum for enterprise deployment |
| **Self-hosted** | Yes -- available as on-premise appliance (B Series, U Series hardware appliances) or cloud-hosted |
| **P2P vs Relay** | Relay through BeyondTrust appliance/cloud. Not P2P |
| **NAT traversal** | Built-in via appliance relay architecture |
| **Unattended access** | Yes -- Jump Clients provide persistent unattended access |
| **Linux support** | Supported. Native client and Jump Clients for Linux |
| **Privacy/data routing** | On-premise appliance keeps all data within your network. Enterprise-grade security and compliance (SOC 2, HIPAA, PCI) |
| **Automation** | API access, scripting, mass deployment, SIEM integration, Active Directory integration |

**Strengths:**
- Enterprise-grade security and compliance certifications
- On-premise appliance option for maximum data control
- Comprehensive audit trail and session recording
- Privileged access management integration
- Very robust platform for regulated industries

**Weaknesses:**
- **Dramatically overpriced for personal use** -- enterprise pricing model with no personal tier
- Opaque pricing requires sales engagement
- Designed for large IT organizations, not personal fleet management
- Hardware appliance model adds cost and complexity
- Massive feature overhead for a 10-machine use case
- No free tier or trial readily available

---

### 9. Screens 5 (Edovia)

| Attribute | Details |
|-----------|---------|
| **Platforms** | Client: macOS, iOS, iPadOS, visionOS. Target: macOS, Windows, Linux, Raspberry Pi (via VNC) |
| **Pricing** | Monthly: $3.99/mo. Annual: $24.99/year. Lifetime: $139.99. One purchase covers Mac, iPhone, iPad |
| **Self-hosted** | Partially. Screens Connect (helper app for Mac/Windows) handles NAT traversal via Edovia's relay. VNC connections can be direct. No self-hosted relay option |
| **P2P vs Relay** | Screens Connect uses relay for NAT traversal. Direct VNC connections possible on LAN or with port forwarding. Tailscale integration recommended for P2P |
| **NAT traversal** | Via Screens Connect helper (relay through Edovia servers) or Tailscale integration |
| **Unattended access** | Yes -- Screens Connect runs in background on target machines |
| **Linux support** | Linux as target only, via VNC. No native Screens Connect helper for Linux -- Edovia recommends using Tailscale for Linux targets. No Linux client |
| **Privacy/data routing** | VNC traffic is direct when on LAN. Screens Connect relay traffic goes through Edovia servers. Tailscale integration provides P2P alternative |
| **Automation** | Minimal. No CLI deployment, no fleet management, no scripting |

**Strengths:**
- Beautiful, polished macOS/iOS native experience
- Affordable pricing ($24.99/year or $139.99 lifetime)
- Tailscale integration is a smart approach to P2P/privacy
- Clipboard sharing, Curtain Mode, file transfer
- Excellent for Apple ecosystem users
- Raspberry Pi support via VNC

**Weaknesses:**
- **macOS/iOS client only** -- cannot connect FROM Windows or Linux
- Linux support is VNC-only with no native helper -- requires Tailscale or manual VNC+port forwarding
- No fleet management or centralized administration
- No SSH integration
- Screens Connect relay goes through Edovia servers (unless using Tailscale)
- Not suitable as the primary tool for a cross-platform fleet -- only works when connecting from Apple devices

---

### 10. Royal TSX

| Attribute | Details |
|-----------|---------|
| **Platforms** | Royal TSX: macOS. Royal TS: Windows. Royal TSi: iOS. Royal TSD: Android. **No Linux client** |
| **Pricing** | Individual license: EUR 49 per platform. Bundle (Windows + Mac): EUR 79. Perpetual license with 12 months maintenance included. Maintenance renewal at 50% discount |
| **Self-hosted** | Not applicable -- Royal TSX is a connection manager, not a remote access service. It uses existing protocols (RDP, VNC, SSH) to connect to targets. No relay infrastructure |
| **P2P vs Relay** | Direct connections only (via RDP, VNC, SSH). No relay service. NAT traversal is the user's responsibility |
| **NAT traversal** | None built-in. Relies on underlying protocol capabilities. User must handle port forwarding, VPN, or tunneling |
| **Unattended access** | Depends on target configuration (RDP, VNC, SSH must be enabled on targets independently) |
| **Linux support** | Can connect TO Linux via SSH/VNC. **No Linux client** -- cannot connect FROM Linux |
| **Privacy/data routing** | Excellent. All connections are direct -- no third-party servers involved. Royal TSX is purely a client application |
| **Automation** | Document sharing via network drives or cloud storage. 1Password/LastPass/KeePass integration. No fleet deployment tools |

**Strengths:**
- Perpetual license (no subscription)
- Pure connection manager -- no third-party relay servers, maximum privacy
- Multi-protocol (RDP, VNC, SSH, S/FTP, web) in a single interface
- Excellent credential management (1Password, LastPass, KeePass integration)
- Shared documents for team use
- AES 256-bit encryption for stored credentials

**Weaknesses:**
- **Not a remote access solution** -- it is a connection manager/client only. Does not solve NAT traversal, unattended access setup, or fleet deployment
- No Linux client
- No built-in NAT traversal or relay
- No agent/host component to install on target machines
- User must independently configure VNC/RDP/SSH on every target and solve NAT traversal separately
- Does not address the core problem of accessing machines behind NATs

---

### 11. NoMachine

| Attribute | Details |
|-----------|---------|
| **Platforms** | Windows, macOS, Linux (Debian, Ubuntu, Red Hat, CentOS, Fedora, and derivatives), iOS, Android, ARM/Raspberry Pi |
| **Pricing** | Free forever for personal/non-commercial use (1 incoming connection). Enterprise Desktop: $44.50/year per machine (unlimited incoming connections). Enterprise server products scale up from there |
| **Self-hosted** | Yes -- fully self-hosted. NoMachine runs entirely on your machines. The free edition is completely self-contained. Enterprise products support VDI deployment |
| **P2P vs Relay** | Hybrid. Uses NX protocol with WebRTC-style hole-punching for P2P connections. Falls back to NoMachine Network relay servers (strategically located worldwide) when hole-punching fails. Supports STUN/TURN -- can self-host your own STUN/TURN server |
| **NAT traversal** | Built-in via multiple methods: UPnP/NAT-PMP (automatic router configuration), WebRTC hole-punching, relay fallback. Also supports reverse SSH tunnels. Self-hosted STUN/TURN server option for full control |
| **Unattended access** | Yes -- NoMachine runs as a service and accepts connections without user interaction. Network subscription enables cloud-registered machine discovery |
| **Linux support** | **Excellent -- Linux is NoMachine's heritage platform** (NX protocol originated as a compressed X11 forwarding technology). Native packages for all major distributions. First-class support |
| **Privacy/data routing** | Self-hosted by default -- no account required for free edition. Connections are direct when possible. Relay fallback goes through NoMachine Network servers. Self-hosted STUN/TURN option eliminates relay dependency entirely. SSH tunneling option for maximum security |
| **Automation** | CLI installation, headless operation, SSH-based connections, configuration files, scripting support |

**Strengths:**
- **Free for personal use** with no nag screens or commercial-use detection
- Linux is a first-class platform (NX protocol heritage)
- Fully self-hosted architecture -- no mandatory cloud dependency
- Self-hosted STUN/TURN option for complete data sovereignty
- Multiple NAT traversal strategies (UPnP, hole-punching, relay, reverse SSH)
- NX protocol provides excellent compression and performance (especially over slow links)
- SSH integration built into enterprise tier
- Browser-based access option (enterprise)
- Headless operation and CLI support
- Enterprise Desktop at $44.50/year/machine is very affordable

**Weaknesses:**
- Free edition limited to 1 incoming connection (only one person can connect at a time)
- Network subscription required for easy machine discovery across the internet (otherwise need IP addresses or DNS)
- UI is functional but dated compared to competitors
- Documentation is comprehensive but can be dense
- NoMachine Network relay is the fallback -- for full P2P you need to self-host STUN/TURN
- Enterprise products require per-machine licensing that adds up ($445/year for 10 machines)
- No centralized fleet management console in the free tier

---

## Comparative Matrix

| Solution | Cross-Platform | Self-Hosted | P2P/Direct | NAT Traversal | Unattended | Linux Quality | Privacy | Cost (10 machines) | Automation |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Remotix** | All | Yes | Hybrid | Via cloud/gateway | Yes | Good | On-prem option | ~$200/yr (1 worker) | Moderate |
| **TeamViewer** | All | No | 70% direct | Excellent | Yes | Good | E2E encrypted, relay | ~$610/yr (Business) | Good |
| **AnyDesk** | All | Yes | Hybrid | Good | Yes | Good | On-prem option | ~$156-312/yr | Good |
| **Parsec** | Partial | No | P2P default | Good | Yes | **No host** | Good (P2P) | Free-$100/yr | Good |
| **Splashtop** | All | Yes | LAN only | Via relay | Yes | Fair | On-prem option | $99/yr (Pro) | Good |
| **Chrome RD** | All | No | WebRTC | Good | Yes | Fair | Google infra | Free | Poor |
| **ScreenConnect** | All (Win server) | Yes (Win) | Via relay | Good | Yes | Fair | Self-hosted option | ~$540-660/yr | Excellent |
| **BeyondTrust** | All | Yes | Via relay | Good | Yes | Good | On-prem appliance | ~$2,000+/yr | Excellent |
| **Screens 5** | Mac client only | Partial | VNC direct | Via relay/Tailscale | Yes | VNC only | Tailscale option | ~$25-140 | Poor |
| **Royal TSX** | No Linux | N/A | Direct only | None | N/A | No client | Excellent | ~$79 (perpetual) | Poor |
| **NoMachine** | All | Yes | Hybrid | Multiple methods | Yes | **Excellent** | Self-hosted | Free-$445/yr | Good |

---

## Analysis Against Requirements

### Requirement 1: Remote Desktop + SSH Access

- **Best:** NoMachine (NX + SSH), ConnectWise ScreenConnect (remote command line), Royal TSX (multi-protocol client)
- **Adequate:** Most solutions handle remote desktop. SSH is typically a separate concern unless the tool integrates it
- **Worst:** Chrome Remote Desktop, Parsec, Screens 5 (desktop only, no SSH)

### Requirement 2: Privacy (Self-Hosted or P2P)

- **Best:** NoMachine (self-hosted + self-hosted STUN/TURN), Royal TSX (direct only, no servers), Remotix On-Premise, AnyDesk On-Premises
- **Adequate:** Parsec Free (P2P default), Chrome Remote Desktop (E2E encrypted)
- **Worst:** TeamViewer (no self-hosted), Splashtop cloud (relay-dependent), BeyondTrust (enterprise pricing for on-prem)

### Requirement 3: Cross-Platform (Linux, macOS, Windows)

- **Best:** NoMachine (Linux heritage, all platforms first-class), TeamViewer, AnyDesk
- **Adequate:** Remotix, Splashtop, Chrome Remote Desktop, ConnectWise ScreenConnect
- **Disqualified:** Parsec (no Linux host), Screens 5 (Mac client only), Royal TSX (no Linux client)

### Requirement 4: NAT Traversal Without Port Forwarding

- **Best:** TeamViewer (just works, 70% direct), NoMachine (UPnP + hole-punching + relay + reverse SSH), Parsec (WebRTC hole-punching)
- **Adequate:** AnyDesk, Chrome Remote Desktop (WebRTC), Splashtop (relay), ConnectWise ScreenConnect (Bridge)
- **Worst:** Royal TSX (none), Screens 5 (requires Tailscale or relay)

### Requirement 5: Non-Technical Family Members (Passive After Setup)

- **Best:** TeamViewer, Splashtop, AnyDesk, Chrome Remote Desktop -- all "install and forget"
- **Adequate:** NoMachine, Remotix, Parsec -- require agent installation but then are passive
- **Worst:** Royal TSX (requires manual VNC/RDP/SSH setup on each target), ConnectWise ScreenConnect (complex MSP-oriented setup)

### Requirement 6: Low Maintenance for ~10 Machines

- **Best:** Splashtop ($99/yr, up to 10 computers, simple), Chrome Remote Desktop (free, simple), TeamViewer (managed console)
- **Adequate:** NoMachine (free, per-machine install), AnyDesk (management console)
- **Worst:** Royal TSX (manual everything), BeyondTrust (enterprise overhead), ConnectWise ScreenConnect (MSP complexity)

### Requirement 7: Automation-Friendly

- **Best:** NoMachine (CLI, config files, headless, SSH), ConnectWise ScreenConnect (scripting, mass deploy), AnyDesk (MSI, custom config)
- **Adequate:** TeamViewer (MSI, group policy), Splashtop (mass deployment), Parsec (CLI, config files)
- **Worst:** Screens 5 (manual only), Royal TSX (no deployment tools), Chrome Remote Desktop (minimal automation)

---

## Recommendations

### Top Tier (Best Fit for Requirements)

**1. NoMachine** -- The strongest overall match. Linux-first heritage means genuinely excellent cross-platform support. Self-hosted by default with no mandatory cloud dependency. Multiple NAT traversal strategies including self-hosted STUN/TURN for complete privacy. Free for personal use. The main trade-offs are a dated UI and the 1-connection limit on the free tier (which is fine if only one person connects at a time). At $44.50/machine/year for enterprise, even the paid tier is reasonable.

**2. Remotix (On-Premise)** -- The current tool, and for good reason. NEAR protocol performance is genuinely superior. On-premise deployment provides full data sovereignty. Multi-protocol flexibility (NEAR, VNC, RDP, Apple Screen Sharing) is unmatched. The primary risks are the Acronis acquisition uncertainty and the $200/year/worker on-premise pricing. If the product remains stable and the on-premise offering persists, this is a strong choice.

### Mid Tier (Good with Trade-offs)

**3. AnyDesk** -- Solid cross-platform support with on-premises option. Direct connections reduce relay dependency. The 2024 security breach and ongoing license model transition are concerns, but the technology is sound.

**4. Splashtop Remote Access Pro** -- Best price-to-value at $99/year for up to 10 computers. However, remote connections always go through Splashtop relay servers (no WAN P2P), making it a poor fit for the privacy requirement. Good choice if privacy is relaxed to "E2E encrypted through relay is acceptable."

**5. TeamViewer** -- Excellent UX and NAT traversal, but no self-hosted option and aggressive commercial-use detection for the free tier. The Business plan at $610/year is expensive. Best if you value "it just works" above privacy and cost.

### Not Recommended for This Use Case

- **Parsec**: No Linux host support -- disqualifying
- **Chrome Remote Desktop**: Free and simple but Google dependency, no fleet management, no SSH, limited Linux support, feels unmaintained
- **ConnectWise ScreenConnect**: Excellent MSP tool but overkill and expensive for personal use; Windows-only server
- **BeyondTrust**: Enterprise pricing and complexity completely mismatched to personal fleet
- **Screens 5**: macOS client only -- cannot be the primary tool for cross-platform fleet
- **Royal TSX**: Connection manager only -- does not solve NAT traversal, unattended access, or deployment

---

## Key Finding

The evaluation reveals a clear gap in the market: **no single commercial product perfectly satisfies all seven requirements simultaneously.** The closest match is **NoMachine**, which checks nearly every box but has UI polish limitations. The optimal strategy is likely **a layered approach**:

1. **NoMachine** (free) as the primary remote desktop solution on all machines -- self-hosted, cross-platform, good NAT traversal
2. **Tailscale or similar mesh VPN** for reliable NAT traversal and SSH access -- creating a private overlay network that makes all machines directly reachable
3. **Remotix/NEAR** retained as a secondary option for high-performance desktop streaming when needed (gaming, video, design work)

This layered approach uses NoMachine's strengths (self-hosted, Linux-first, free) while offsetting its NAT traversal limitations with a purpose-built mesh networking layer, and retaining Remotix's NEAR protocol for performance-critical use cases.
