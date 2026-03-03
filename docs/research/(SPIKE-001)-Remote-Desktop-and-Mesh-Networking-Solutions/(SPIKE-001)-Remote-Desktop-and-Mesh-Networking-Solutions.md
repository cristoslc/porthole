---
artifact: SPIKE-001
title: Remote Desktop and Mesh Networking Solutions for Personal Fleet
status: Complete
author: cristos
created: 2026-02-27
last-updated: 2026-02-27
parent-epic: EPIC-001
depends-on: []
---

# SPIKE-001: Remote Desktop and Mesh Networking Solutions for Personal Fleet

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-27
**Last Updated:** 2026-02-27
**Parent:** [EPIC-001](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Blocks:** [ADR-003](../../adr/Abandoned/(ADR-003)-Network-Layer-for-Remote-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-27 | 6df2003 | Research conducted and documented in a single session |

---

## Question

What are the viable open-source remote desktop and mesh/overlay networking solutions for a personal fleet of ~10 machines across Linux, macOS, and Windows, evaluated against the requirements in VISION-001 (privacy, self-hosting, cross-platform, NAT traversal, family-friendliness, automation)?

## Gate

Pre-ADR-003 decision. This spike informs the network layer recommendation and validates the RustDesk choice (ADR-001).

### Go criteria

- At least 3 remote desktop solutions and 3 mesh networking solutions evaluated with current (2025-2026) data.
- Each solution assessed against: platforms, self-hosting, maturity, NAT traversal, unattended access, Linux quality, family-friendliness, and notable limitations.

### No-go pivot

Not applicable -- this is an informational spike, not a gating decision. Findings feed into ADR-003.

## Risks addressed

- Choosing a tool that lacks cross-platform support or is abandoned upstream.
- Overlooking a superior alternative to RustDesk or Tailscale.
- Underestimating operational complexity of self-hosted options.

## Dependencies

- None. This spike is pure research.

---

## Findings: Remote Desktop Solutions

### 1. RustDesk (Selected -- ADR-001)

**Summary:** Open-source remote desktop application designed as a self-hosted TeamViewer/AnyDesk alternative. Written in Rust. The project has already been adopted via ADR-001.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux, macOS, Windows, Android, iOS. All first-class. |
| **Self-hosted** | Yes. OSS server (hbbs + hbbr) is free, unlimited devices. Pro server ($9.90/mo) adds web console, address book, OIDC, audit logs. The relay component (hbbr) is identical between OSS and Pro. |
| **Maturity** | Very active. v1.4.3 (Oct 2025) added multi-monitor Wayland support and virtual mouse. GitHub: 80k+ stars. AGPL-3.0 license. |
| **NAT traversal** | Built-in hole-punching. Relay fallback via hbbr if hole-punching fails. When paired with a mesh VPN (Tailscale), direct IP mode bypasses all RustDesk infrastructure entirely. |
| **Unattended access** | Permanent password support. CLI flags: `--silent-install`, `--password`, `--config`, `--import-config`. Systemd service on Linux. |
| **Linux quality** | Good on X11. Wayland support is experimental and improving: multi-monitor works since v1.4.3, but Wayland-to-Wayland clipboard is broken, login-screen capture is not supported, and some distros trigger "Wayland requires higher version" errors. |
| **Family-friendliness** | Moderate. Non-technical users can accept incoming connections after initial setup. The operator connects to them -- they do not need to initiate anything. |
| **Automation** | `.deb` install, config file templating, systemd integration -- standard Ansible patterns. No apt repo; updates require re-downloading from GitHub releases. |

**Notable limitations:**
- Own protocol only -- cannot connect to VNC/RDP servers. Remmina (Linux) or built-in OS tools (macOS/Windows) needed for VNC/RDP.
- macOS permissions (Screen Recording, Accessibility) must be granted manually via System Settings. Known issues: the "Configure" button sometimes does nothing; black screen on connection despite permissions being granted. Workaround: manual TCC database commands in Terminal.
- `.deb` from GitHub releases, not an apt repo -- no automatic security updates.
- Wayland clipboard and login-screen issues remain as of early 2026.

**RustDesk + Tailscale integration:** Tailscale published official documentation for this combination. RustDesk's Direct IP mode uses Tailscale's 100.x.y.z addresses. Tailscale handles authentication, NAT traversal, hole-punching, and fallback relay (DERP). RustDesk's dependency on its own relay and ID servers is completely eliminated.

---

### 2. Apache Guacamole

**Summary:** Clientless (HTML5 browser-based) remote desktop gateway. The server-side daemon (guacd) speaks RDP, VNC, SSH, and Telnet to backend machines and translates everything to a browser-rendered protocol.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux only (guacd). Client: any web browser on any OS. Backend targets: anything speaking VNC, RDP, or SSH. |
| **Self-hosted** | Yes. Fully self-hosted. Apache 2.0 license. Docker images available (including ARM since v1.6.0). |
| **Maturity** | Active. v1.6.0 released June 2025. Apache Software Foundation project. Major protocol optimizer rewrite in 1.6.0 improved responsiveness and reduced bandwidth. |
| **NAT traversal** | None built-in. Guacamole is a gateway server -- it must be able to reach backend machines directly (on the same network or via VPN). No agent, no hole-punching. SSH tunnels to backends must be configured manually outside Guacamole. |
| **Unattended access** | Yes, inherently -- Guacamole connects to always-running VNC/RDP/SSH servers on backends. But those servers must be separately installed and configured. |
| **Linux quality** | guacd is Linux-native. Excellent quality. |
| **Family-friendliness** | Excellent for the client side (just open a browser). Poor for setup -- requires deploying a Tomcat/Java web app + guacd + database, and separately provisioning VNC/RDP servers on every target machine. |
| **Automation** | Docker Compose deployment. Connection definitions via database or YAML. No agent to push -- but also no agent to handle NAT. |

**Notable limitations:**
- Not a remote desktop tool -- it is a gateway/proxy. It requires VNC, RDP, or SSH servers to already be running and reachable on the target machines.
- No NAT traversal whatsoever. Guacamole must be on the same network (or VPN) as its targets. Cannot reach machines behind NAT without a VPN layer.
- No peer-to-peer capability. All traffic routes through the Guacamole server.
- Heavy infrastructure for a personal fleet: Java/Tomcat, PostgreSQL or MySQL, guacd, plus VNC/RDP servers on every target.
- SSH agent forwarding requires patching libssh2.

**Verdict for this fleet:** Not suitable as a primary tool. It solves a different problem (browser-based access to servers in a data center). Could complement RustDesk as a web-based fallback for SSH access if deployed behind the mesh VPN, but the infrastructure weight is disproportionate for ~10 machines.

---

### 3. MeshCentral

**Summary:** Full-featured, self-hosted web-based remote monitoring and management (RMM) platform. Node.js server with native agents for Windows, Linux, and macOS. Provides remote desktop, terminal, file management, and device monitoring through a web browser.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux (Node.js). Agent: Windows, Linux, macOS (Intel + Apple Silicon). |
| **Self-hosted** | Yes. Fully self-hosted. Apache 2.0 license. No cloud dependency. |
| **Maturity** | Very active. v1.1.56 (Jan 2026). Regular releases (multiple per month). Created by Ylian Saint-Hilaire (ex-Intel). 4k+ GitHub stars. |
| **NAT traversal** | Yes. Agents maintain persistent outbound WebSocket connections to the server. Reverse tunneling through the server handles all NAT scenarios. No port forwarding needed on agent machines. |
| **Unattended access** | Yes. Agents run as system services. Full remote desktop, terminal, and file access without user interaction on the remote end. |
| **Linux quality** | Good. Native agent binary. Terminal and file management work well. |
| **Family-friendliness** | Moderate. Agent install is straightforward (download + run). But the platform is designed for IT administrators -- the web UI is functional but complex. |
| **Automation** | Agent install via URL/script. Server deploys via npm or Docker. Mesh agent can be mass-deployed. REST API available. |

**Notable limitations:**
- macOS agent has documented issues: cannot click (only move mouse) on some versions, agent fails to start after macOS Ventura update, permissions for screen recording and accessibility must be manually granted.
- All remote desktop traffic routes through the MeshCentral server (not peer-to-peer). The server is a bandwidth bottleneck and single point of failure.
- The web-based remote desktop viewer has noticeable latency compared to native RDP/VNC clients or RustDesk.
- The UI is powerful but overwhelming for simple use cases. Designed for MSPs managing hundreds of devices, not a personal fleet of 10.
- No built-in mesh networking or VPN capability -- it provides remote access, not network connectivity. SSH to arbitrary ports still requires a VPN layer.

**Verdict for this fleet:** A strong alternative to RustDesk if you want an all-in-one RMM with web-based access. However, server-routed traffic (not P2P), macOS agent reliability issues, and UI complexity make it less suitable than RustDesk + mesh VPN for this use case. Worth revisiting if the fleet grows or monitoring/management needs expand.

---

### 4. TigerVNC / TurboVNC

**Summary:** Open-source VNC server and client implementations, both descended from TightVNC. TigerVNC is the general-purpose workhorse; TurboVNC is optimized for high-performance GPU-accelerated graphics (3D, CAD, video) via VirtualGL integration.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Both: Linux, Windows, macOS (server and client). |
| **Self-hosted** | Yes. Fully local. No cloud component. |
| **Maturity** | TigerVNC: moderately active, incremental releases. TurboVNC: actively maintained, focused on HPC/GPU workloads. Both are stable, long-lived projects. |
| **NAT traversal** | None. VNC is a direct-connection protocol. Requires port forwarding or a VPN to reach machines behind NAT. |
| **Unattended access** | Yes. VNC server runs as a system service. Password-protected. |
| **Linux quality** | Excellent on X11. TigerVNC is the default VNC server on many Linux distributions. Neither supports Wayland natively. |
| **Family-friendliness** | Poor. Requires manual server configuration, firewall rules, and password setup. Client must know the IP and port. No discovery, no address book. |
| **Automation** | Package manager install. Config files. Straightforward but manual. |

**Key differences:**
- TigerVNC: Tight encoding, good for general desktop use, moderate bandwidth.
- TurboVNC: JPEG compression tuned for large visual workloads, 3-4x faster for 3D/video content, built-in VirtualGL integration. Uses ~15-20% of the CPU compared to TightVNC for the same content.

**Notable limitations:**
- No NAT traversal, no relay, no hole-punching. Completely dependent on direct network reachability.
- No Wayland support. X11 only. As GNOME 47+ drops X11 entirely and distros default to Wayland, these tools become increasingly limited on modern Linux desktops.
- No integrated client+server+relay architecture. You assemble separate components yourself.
- No encryption by default (must tunnel over SSH or use TLS configuration).
- No mobile clients (community viewers exist but are not maintained by the projects).

**Verdict for this fleet:** Not suitable as a primary remote desktop solution. No NAT traversal, no Wayland, no integrated architecture. Useful as a fallback VNC server on X11 Linux machines, already covered by Remmina on the client side. TurboVNC is relevant only for GPU workloads (not applicable here).

---

### 5. x11vnc + VNC Viewers

**Summary:** x11vnc attaches to an existing X11 display and shares it over VNC. Unlike TigerVNC (which creates a virtual display), x11vnc shares the physical display -- what you see on the monitor is what the remote user sees.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux only (X11). Clients: any VNC viewer on any platform. |
| **Self-hosted** | Yes. Fully local. |
| **Maturity** | Maintenance mode. Original author (Karl Runge) stopped development. LibVNC community maintains it on GitHub. Last significant update: 2019 (v0.9.16). |
| **NAT traversal** | None. Same as TigerVNC -- direct connection only. |
| **Unattended access** | Yes, can run as a daemon. |
| **Linux quality** | Good on X11. Wayland support is minimal -- only via `-rawfb` and a bundled `deskshot` utility, which is a hack, not real Wayland support. |
| **Family-friendliness** | Poor. Command-line tool. No GUI, no discovery. |
| **Automation** | CLI flags for everything. Scriptable but low-level. |

**Notable limitations:**
- Effectively dead upstream. No meaningful development since 2019.
- X11 only. As GNOME dropped X11 support in November 2025, x11vnc has no future on modern GNOME desktops.
- No encryption by default (must tunnel over SSH).
- No NAT traversal.
- Shares only the physical display -- cannot create virtual sessions.

**Verdict for this fleet:** Not recommended. Unmaintained, X11-only, no NAT traversal. Superseded by RustDesk for this use case. The X11-to-Wayland transition makes x11vnc a dead end.

---

### 6. SPICE (Simple Protocol for Independent Computing Environments)

**Summary:** Remote display protocol designed for virtual machines. Originally developed by Qumranet, open-sourced by Red Hat in 2009. Provides high-quality video, audio, USB redirection, clipboard sharing, and seamless cursor movement between host and guest.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux (QEMU/KVM integration). Clients: Linux (virt-viewer, remote-viewer), Windows, HTML5 (via spice-html5). |
| **Self-hosted** | Yes. Integral to KVM/QEMU/Proxmox virtualization stacks. |
| **Maturity** | Mature and stable. Actively maintained as part of the QEMU/libvirt ecosystem. Used in production by Proxmox, oVirt, and OpenStack. |
| **NAT traversal** | None. Direct connection to the hypervisor. Designed for LAN or VPN access to VM consoles. |
| **Unattended access** | Yes, inherently -- VMs are always running and SPICE is always available through the hypervisor. |
| **Linux quality** | Excellent within the VM context. |
| **Family-friendliness** | Not applicable. This is a VM console protocol, not a general-purpose remote desktop tool. |
| **Automation** | Configured via libvirt XML or Proxmox API. |

**Notable limitations:**
- Designed exclusively for virtual machines. Cannot share a physical desktop.
- Requires a hypervisor (QEMU/KVM). Not applicable to bare-metal macOS or Windows machines.
- No NAT traversal. The hypervisor must be reachable.

**Verdict for this fleet:** Not applicable. SPICE is for VM consoles, not for connecting to physical desktops across a fleet. Already available implicitly through Proxmox for any VMs on the home server.

---

### 7. Remmina (Client Only)

**Summary:** GTK-based remote desktop client for Linux. Multi-protocol frontend -- not a server.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux only. |
| **Protocols** | RDP (via FreeRDP), VNC, SSH, SPICE, NX, XDMCP, X2Go. Plugin architecture allows adding more. |
| **Maturity** | Active. Available via Flatpak, Snap, and distro repos. Regular updates. |
| **Self-hosted** | N/A -- client only. Connects to existing servers (RDP, VNC, SSH, SPICE endpoints). |
| **Family-friendliness** | Moderate. GUI with saved connection profiles. But requires knowing server addresses and protocols. |

**Notable limitations:**
- Linux only. No macOS or Windows version.
- Client only -- does not make a machine controllable. Requires VNC/RDP/SSH servers on target machines.
- Cannot connect to RustDesk endpoints (different protocol).

**Verdict for this fleet:** Already installed by SPEC-002 (formerly PRD-002) as a complementary client for VNC/RDP connections. Not a primary tool -- it talks to servers that must be separately provisioned. Useful for connecting to Windows RDP, Proxmox SPICE, or legacy VNC servers.

---

### 8. FreeRDP / xrdp

**Summary:** FreeRDP is an open-source RDP client (and library). xrdp is an open-source RDP server for Linux that allows Windows Remote Desktop clients to connect to Linux machines.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | FreeRDP client: Linux, macOS, Windows. xrdp server: Linux only. |
| **Self-hosted** | Yes. Fully local. |
| **Maturity** | FreeRDP: very active, v3.20.1 (Jan 2026). Multiple releases per month. xrdp: active, v0.10.4.1 (Jul 2025). |
| **NAT traversal** | None. RDP is a direct-connection protocol. |
| **Unattended access** | xrdp runs as a system service on Linux. Windows has built-in RDP server (Pro/Enterprise only). |
| **Linux quality** | FreeRDP client: excellent. xrdp server: good on X11, but no Wayland support. This is a significant gap -- xrdp cannot serve Wayland sessions, and Ubuntu 26.04 defaults to Wayland. |
| **Family-friendliness** | Moderate. RDP is familiar to Windows users. But xrdp setup on Linux requires configuration. |
| **Automation** | Package manager install. Config files. Standard. |

**FreeRDP Wayland client status:** FreeRDP has a `wlfreerdp` Wayland client, but it has been deprecated. The `xfreerdp` client works on Wayland (via XWayland). An SDL3-based client is being developed as the successor.

**Notable limitations:**
- xrdp does not support Wayland sessions. As Linux distros move to Wayland by default, xrdp users must install X11-based desktop environments for remote sessions.
- No NAT traversal. Direct connection only.
- Windows Home edition does not include RDP server. Only Pro/Enterprise.
- No integrated relay or discovery mechanism.

**Verdict for this fleet:** FreeRDP is useful as an RDP client (already available via Remmina). xrdp could serve Linux machines to Windows RDP clients, but the Wayland gap and lack of NAT traversal make it unsuitable as a primary solution. RustDesk covers this use case better.

---

### 9. WayVNC

**Summary:** A VNC server for wlroots-based Wayland compositors (Sway, Wayfire, etc.). The Wayland-native answer to x11vnc.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux only (wlroots compositors). Clients: any VNC viewer. |
| **Self-hosted** | Yes. Fully local. |
| **Maturity** | Active. v0.9 released with ext-image-copy-capture-v1 support, hardware encoding on Raspberry Pi, improved clipboard handling. |
| **NAT traversal** | None. VNC direct connection only. |
| **Unattended access** | Yes, can run headless (no physical display required). |
| **Linux quality** | Good, but only for wlroots-based compositors (Sway, Wayfire). Does NOT work with GNOME (Mutter) or KDE (KWin) -- they are not wlroots-based. |
| **Family-friendliness** | Poor. Command-line tool. Requires a wlroots compositor. |
| **Automation** | CLI-driven. Config file support. |

**Notable limitations:**
- wlroots-only. Does not work with GNOME or KDE Plasma -- the two most popular Linux desktop environments. This is a fundamental architectural limitation, not a missing feature.
- No NAT traversal.
- No encryption by default (must tunnel over SSH or use TLS).
- Niche use case: only relevant if you run Sway or another wlroots compositor.

**Verdict for this fleet:** Not applicable for this fleet. Family machines almost certainly run GNOME or KDE, not Sway. Even on the operator's machines, RustDesk provides better cross-platform coverage. WayVNC is relevant only for Sway power users who want native Wayland VNC.

---

### 10. DWService

**Summary:** Browser-based remote access service with a lightweight agent. The operator controls remote machines through a web browser; agents are installed on target machines.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Agent: Windows, macOS, Linux, Raspberry Pi. Client: any web browser. |
| **Self-hosted** | Partially. The agent is open source (MPLv2 core). However, DWService only works through their cloud service -- there is no self-hosted server option. Users can volunteer to run relay nodes, but the control plane is SaaS-only. |
| **Maturity** | Active. Regular updates. Growing community. |
| **NAT traversal** | Yes, handled by DWService cloud. Agents connect outbound to the DWService relay network. |
| **Unattended access** | Yes. Agent runs as a system service. |
| **Linux quality** | Good. Native agent. |
| **Family-friendliness** | Good for the client side (just open a browser). Agent install is straightforward. |
| **Automation** | Agent install via script. Limited CLI configuration. |

**Notable limitations:**
- Not self-hostable. All traffic routes through DWService's cloud relay servers. This directly violates the privacy requirement (VISION-001 success metric 4: "Zero session traffic transits third-party infrastructure").
- Free tier has bandwidth limitations. Paid subscription or running a relay node unlocks 20 Mbps maximum bandwidth.
- Cloud dependency means availability depends on DWService's infrastructure.

**Verdict for this fleet:** Disqualified. Cannot be self-hosted. All session traffic passes through third-party relay servers. Violates the core privacy requirement.

---

### 11. HopToDesk (RustDesk Fork)

**Summary:** Fork of RustDesk launched in 2022 by Begonia Holdings LLC. AGPL-3.0 licensed (signaling server: MIT). Aims to be a mass-market alternative to TeamViewer/AnyDesk.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Windows, macOS, Linux, Android, iOS, ChromeOS, Raspberry Pi. |
| **Self-hosted** | Partial. Self-hosting via Cloudflare Workers or on-premises. HopSignal (signaling server) is MIT-licensed. Users can configure their own TURN server for relay. |
| **Maturity** | Active but smaller community than RustDesk. Published on Flathub (2024). GitLab-hosted. Less transparent development history -- community has raised concerns about attribution and missing features compared to upstream RustDesk. |
| **NAT traversal** | Same as RustDesk (hole-punching + relay fallback). |
| **Unattended access** | Reported issues: Windows service for unattended access has been flagged as missing or unreliable in community reports. |
| **Linux quality** | Same as RustDesk (shared codebase origin). |
| **Family-friendliness** | Similar to RustDesk. Dashboard feature for monitoring saved devices is a usability improvement. |
| **Automation** | Similar to RustDesk. |

**Notable limitations:**
- Community trust concerns: RustDesk community discussions have raised warnings about HopToDesk's transparency regarding its fork lineage and missing features.
- Smaller development team and community than RustDesk.
- Self-hosting documentation is less mature than RustDesk's.
- The unattended access story (Windows service) has been questioned.
- AWS/Cloudflare deployment model may not appeal to users wanting fully on-premises hosting.

**Verdict for this fleet:** No compelling advantage over upstream RustDesk. Smaller community, less transparency, and community trust concerns. RustDesk is the better-supported choice. If RustDesk were abandoned, HopToDesk would be a viable fork to evaluate, but that scenario is unlikely given RustDesk's momentum.

---

## Findings: Mesh / Overlay Networking Solutions

### 1. Tailscale (Commercial, SaaS Control Plane)

**Summary:** WireGuard-based mesh VPN with automatic NAT traversal, key management, and a SaaS control plane. The gold standard for zero-configuration mesh networking.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux, macOS, Windows, iOS, Android, FreeBSD, OpenBSD, Synology, QNAP. All first-class. |
| **Self-hosted** | Partial. The client (`tailscaled`) is open source (BSD-3-Clause). The control plane (coordination server) is proprietary SaaS. DERP relay servers can be self-hosted. |
| **Maturity** | Production-grade. Used by thousands of organizations. Very active development. Changelog shows multiple releases per month in 2025-2026. |
| **NAT traversal** | Best-in-class. Automatic hole-punching (STUN/ICE). DERP relay fallback when direct connections fail. Published detailed technical documentation on their NAT traversal approach. |
| **Free tier** | Personal plan: 3 users, 100 devices, free. Personal Plus: 6 users, 100 devices, $5/mo. Free tier includes tag-based ACLs, MagicDNS, Tailscale SSH. |
| **Linux quality** | Excellent. Native package for all major distros. `tailscaled` as systemd service. |
| **Family-friendliness** | Excellent. Install app, sign in (or paste pre-auth key), done. No configuration needed. |
| **Automation** | CLI (`tailscale up --authkey=...`), config-as-code for ACLs (via `tailscale.com/acls`), pre-auth keys for headless enrollment. |

**Notable strengths:**
- MagicDNS: human-readable hostnames (`hostname.tailnet-name.ts.net`) resolve automatically.
- Tailscale SSH: eliminates SSH key management entirely -- SSH over WireGuard with identity-based auth.
- Subnet routers: expose a LAN without installing Tailscale on every device.
- Exit nodes: route internet traffic through a specific node.
- Device count optimization: use subnet routers instead of per-container Tailscale to stay within the 100-device limit.

**Notable limitations:**
- Proprietary control plane. Device registration, key exchange, and ACL management go through Tailscale's servers. The control plane does NOT see traffic content (WireGuard encryption is end-to-end), but it knows which devices exist and their network topology.
- Vendor lock-in risk. The control plane is SaaS-only (no self-hosted option from Tailscale themselves).
- 100-device limit on free tier. Docker containers and VMs each count as a device if running `tailscaled`.
- RustDesk does not resolve MagicDNS names -- must use raw 100.x.y.z IPs.

**Escape hatch:** Headscale (see below) provides a self-hosted control plane compatible with official Tailscale clients. Migration requires no client-side changes.

---

### 2. Headscale (Self-Hosted Tailscale Control Plane)

**Summary:** Open-source, self-hosted implementation of the Tailscale coordination server. Allows running official Tailscale clients against your own infrastructure instead of Tailscale's SaaS.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Server: Linux (single binary or Docker). Clients: official Tailscale clients on all platforms (Linux, macOS, Windows, iOS, Android). |
| **Self-hosted** | Yes. Fully self-hosted. BSD-3-Clause license. |
| **Maturity** | Active. v0.28.0 (Feb 2026). Maintained by Kristoffer Dalby and Juan Font. Tailscale Inc. collaborates with Headscale maintainers on client compatibility. |
| **NAT traversal** | Same as Tailscale. Embedded DERP relay server. Can also use Tailscale's public DERP infrastructure or self-host additional DERP relays. |
| **Free tier** | Entirely free. No device limits. No user limits. |
| **Linux quality** | Server is a single Go binary. Uses official Tailscale clients -- same quality as Tailscale. |
| **Family-friendliness** | Moderate. Clients are the same Tailscale apps. But enrollment requires pointing the client at your Headscale instance URL instead of Tailscale's -- slightly more complex than "just sign in." |
| **Automation** | CLI (`headscale`) for user/node management. REST API. OIDC authentication support since v0.24. |

**What Headscale has:**
- Base Tailscale feature parity: WireGuard mesh, ACLs, MagicDNS, exit nodes, subnet routers.
- Embedded DERP relay for NAT traversal fallback.
- OIDC authentication.
- Web UI via Headplane (community project, v0.6).

**What Headscale is missing (vs. Tailscale SaaS):**
- Funnel and Serve (beta features for exposing services to the internet).
- Network flow logs.
- Dynamic ACL support.
- OIDC groups in ACLs.
- Global DERP relay infrastructure (you must self-host or use Tailscale's public relays).
- Tailscale's polished admin console.

**Notable limitations:**
- Requires a server with a stable public IP (IPv4+IPv6). CGNAT makes this difficult in some locations. A cheap VPS ($3-5/mo) solves this.
- Operational overhead: you run the coordination server, manage backups, handle upgrades. Tailscale SaaS does this for free.
- Single-tailnet scope: designed for personal use or small organizations, not multi-tenant.
- Mobile enrollment is more complex than Tailscale SaaS (must specify control server URL).

**Verdict for this fleet:** The best escape hatch from Tailscale SaaS. Same client apps, same UX, no device limits, no cost. Recommended as the documented fallback per ADR-003. Not recommended as the primary choice because the operational overhead of running a coordination server is unnecessary when Tailscale's free tier meets all requirements.

---

### 3. ZeroTier

**Summary:** Software-defined networking platform that creates virtual Layer 2 Ethernet networks. Devices join a 16-digit network ID and receive virtual IP addresses. Supports both cloud-hosted and self-hosted controllers.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux, macOS, Windows, iOS, Android, FreeBSD, NAS devices (Synology, QNAP, TrueNAS). |
| **Self-hosted** | Partial with caveats. The client (`zerotier-one`) was open source (BSL-1.1). As of v1.16.0 (Aug 2025), the network controller source code is now under a commercial source-available license. Self-hosted controllers using the old open-source code still work. Web UIs: ztncui, ZeroUI, ZTNET. |
| **Maturity** | Mature. v1.16.0 (Sep 2025). Long-lived project (founded 2011). Redesigned Central UI (Nov 2025). |
| **NAT traversal** | Good. Automatic hole-punching. Root servers (planet) coordinate connections. Moon servers can be self-hosted for private root infrastructure. Relay fallback through root servers. |
| **Free tier (cloud)** | 10 devices, 1 network, free. Essential: $18/mo + $2/device beyond 10. Self-hosted controller: no device limits (but see licensing caveat). |
| **Linux quality** | Good. Native packages for major distros. |
| **Family-friendliness** | Moderate. Install app, enter 16-digit network ID, wait for admin approval. Slightly more steps than Tailscale (no "just sign in" flow). |
| **Automation** | CLI (`zerotier-cli`). REST API for controller. Docker support. |

**Notable strengths:**
- Layer 2 support: broadcast, multicast, mDNS. Useful for service discovery.
- Devices can be in both ZeroTier and Tailscale simultaneously (different tun interfaces).
- Self-hosted controller has no device limits.
- Flow Rules for fine-grained network policy.

**Notable limitations:**
- Licensing change in v1.16.0: the network controller is no longer open source. Default builds no longer include the controller. Self-hosting now requires either using older open-source builds or the commercial source-available license.
- Custom protocol (not WireGuard). Smaller security audit surface than WireGuard. Slower community adoption.
- Cloud free tier is only 10 devices -- borderline for a ~12 machine fleet.
- Flow Rules syntax is less intuitive than Tailscale ACLs.
- Family onboarding requires an additional approval step (admin must authorize the device).
- ZeroTier Central (cloud) is a SaaS dependency. Self-hosted controller removes this but adds operational burden.

**Verdict for this fleet:** A strong alternative, documented as the primary fallback in ADR-003. True network-level separation from the existing Tailscale tailnet. The licensing change in v1.16.0 is a concern for long-term self-hosting viability. If chosen, use the self-hosted controller to avoid the 10-device cloud limit.

---

### 4. Nebula (by Slack / Defined Networking)

**Summary:** Certificate-based overlay networking tool focused on performance, simplicity, and security. Created at Slack, open-sourced in 2019. Uses the Noise Protocol Framework for mutual authentication.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux, macOS, Windows, iOS, Android. |
| **Self-hosted** | Yes. Fully self-hosted. MIT license. No cloud dependency (though Defined Networking offers a commercial management layer). |
| **Maturity** | Active. v1.10.0 on GitHub. Maintained by Defined Networking. Still powers Slack's production network (50k+ hosts). |
| **NAT traversal** | Automatic hole-punching between peers. Lighthouse nodes coordinate peer discovery. Relay support is limited compared to Tailscale/ZeroTier. |
| **Free tier** | Entirely free. No device limits. |
| **Linux quality** | Good. Single binary. |
| **Family-friendliness** | Poor. Certificate-based enrollment requires generating keypairs, signing certificates with a CA, and distributing config files. No "install and sign in" flow. |
| **Automation** | CLI for cert generation. YAML config files. Ansible-friendly but requires significant upfront work. |

**Notable limitations (documented in community reviews, 2025):**
- Mobile client is severely limited: no firewall rules on iOS, no always-on VPN, cannot upload pre-signed certificates (must export public key, sign externally, re-import).
- DNS is primitive: lighthouses only resolve node names dynamically, no custom DNS override.
- Certificate management is manual and complex. No built-in rotation or renewal.
- "Not aimed at small organizations and hobbyists" (community assessment, Sep 2025). Feature set lags Tailscale significantly.
- No web UI for management (unless using Defined Networking's commercial product).
- Family onboarding is impractical: non-technical users cannot generate keypairs and manage certificates.

**Verdict for this fleet:** Not recommended. Certificate management complexity and poor family onboarding make it unsuitable for this use case. Nebula is designed for large infrastructure networks (like Slack's), not personal fleets with non-technical users. Tailscale/Headscale and ZeroTier are strictly better choices for this scenario.

---

### 5. WireGuard (Raw) + Management UIs

**Summary:** WireGuard is an in-kernel VPN protocol. It is not a mesh network -- it creates point-to-point tunnels. Management UIs like wg-easy, Firezone, and others add peer management, web interfaces, and simplified configuration.

#### WireGuard (raw)

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux (in-kernel since 5.6), macOS, Windows, iOS, Android, FreeBSD, OpenBSD. |
| **Self-hosted** | Yes. Fully self-hosted. GPL-2.0. |
| **Maturity** | Production-grade. In the Linux kernel. Battle-tested. |
| **NAT traversal** | None built-in. WireGuard endpoints must be reachable. Requires port forwarding or a publicly reachable hub. |
| **Family-friendliness** | Very poor (raw). Requires generating keypairs, editing config files, managing IP allocation manually. |

#### wg-easy

| Attribute | Assessment |
|-----------|------------|
| **What it is** | Docker-based WireGuard server + web UI for peer management. |
| **Maturity** | Active. 17k+ GitHub stars. v15.1 as of late 2025. |
| **Features** | List/create/edit/delete/enable/disable clients, QR code generation, config file download, Tx/Rx charts. |
| **Limitations** | Hub-and-spoke only (not mesh). Hub must be publicly reachable. No automatic NAT traversal between peers. |

#### Firezone

| Attribute | Assessment |
|-----------|------------|
| **What it is** | Enterprise zero-trust access platform built on WireGuard. Open source (Apache 2.0). YC W22. |
| **Maturity** | Active. Last update Dec 2025. |
| **Features** | SSO/OIDC, MFA, granular access policies, automatic load balancing, nftables egress control. 3-4x faster than OpenVPN. |
| **Self-hosted** | Open source, technically self-hostable, but internal APIs are changing rapidly and the team cannot meaningfully support self-hosting in production at this time. |
| **Limitations** | Self-hosting is unsupported and unstable. Primarily designed as a SaaS product. Enterprise-focused (SSO, group policies) -- overkill for a personal fleet. |

**Verdict for raw WireGuard:** Rejected as Option C in ADR-003. Maximum sovereignty but maximum operational burden. Manual key management, no NAT traversal, impractical for non-technical family members. Headscale (self-hosted Tailscale) provides the same WireGuard transport with dramatically less operational friction.

**Verdict for wg-easy:** Useful if you need a simple WireGuard server with a web UI. But it is hub-and-spoke (not mesh), requires the hub to be publicly reachable, and provides no NAT traversal between peers. Not suitable for a distributed fleet behind various NATs.

**Verdict for Firezone:** Not recommended. Self-hosting is explicitly unsupported. Enterprise-focused features (SSO, group policies) are unnecessary for a personal fleet. The product direction is SaaS, not self-hosted.

---

### 6. NetBird

**Summary:** Open-source zero-trust networking platform built on WireGuard. Combines mesh VPN, access control, and SSO into a single product. Both client and server are fully self-hostable.

| Attribute | Assessment |
|-----------|------------|
| **Platforms** | Linux, macOS, Windows, iOS, Android, Docker, FreeBSD. |
| **Self-hosted** | Yes. Fully self-hosted (client + management server + signal server + relay). Apache 2.0 license. |
| **Maturity** | Very active. v1.26.0 (Feb 2026). Rapidly growing. Architecture documented in detail. Benchmarks show support for 10k peers with sub-millisecond latency. |
| **NAT traversal** | Automatic. WireGuard tunnels with ICE-based NAT traversal. Relay fallback via self-hosted TURN servers. |
| **Free tier (cloud)** | Free for up to 5 users, 100 peers. |
| **Linux quality** | Excellent. Native packages. systemd integration. |
| **Family-friendliness** | Good. Desktop app with SSO login. Similar ease to Tailscale. Self-hosted instance requires pointing the client at your server URL. |
| **Automation** | CLI (`netbird`), REST API, setup keys for headless enrollment, Docker Compose for server deployment. |

**Notable strengths:**
- Fully self-hostable: management server, signal server, TURN relay -- all open source.
- Built-in reverse proxy for exposing services through the mesh.
- SSO integration (OIDC) for user authentication.
- Network segmentation via access policies.
- Web UI for administration.
- "5-minute self-hosted setup" via Docker Compose.

**Notable limitations:**
- Younger project than Tailscale or ZeroTier. Smaller community. Moving fast -- API changes between versions.
- Self-hosted deployment has more components than Headscale (management server + signal server + TURN relay vs. single Headscale binary).
- Uses its own control plane protocol -- not compatible with Tailscale clients (unlike Headscale).
- Documentation is improving but less comprehensive than Tailscale's.
- No equivalent of Tailscale SSH or MagicDNS (though DNS is in development).

**Verdict for this fleet:** The most cohesive fully-self-hosted mesh VPN option. If the goal were to avoid any SaaS dependency from day one, NetBird would be the top choice. However, for this fleet, Tailscale's free tier meets all requirements with zero operational overhead, and Headscale provides a lighter-weight escape hatch than NetBird's multi-component self-hosted stack. NetBird is worth monitoring as it matures -- it may become the recommended choice if Tailscale's terms change.

---

## Comparative Summary

### Remote Desktop Solutions

| Solution | Cross-Platform | Self-Hosted | NAT Traversal | Wayland | Family-Friendly | Verdict |
|----------|---------------|-------------|---------------|---------|-----------------|---------|
| **RustDesk** | Linux/Mac/Win | Yes (OSS relay) | Yes (hole-punch + relay) | Partial (improving) | Moderate | **Selected (ADR-001)** |
| Apache Guacamole | Server: Linux; Client: browser | Yes | None | N/A (gateway) | Client: good; Setup: poor | Not suitable (no NAT, heavy infra) |
| MeshCentral | Linux/Mac/Win | Yes | Yes (reverse tunnel) | N/A (web viewer) | Moderate | Strong alternative; server-routed traffic, macOS issues |
| TigerVNC / TurboVNC | Linux/Mac/Win | Yes | None | No (X11 only) | Poor | Not suitable (no NAT, no Wayland) |
| x11vnc | Linux only | Yes | None | Minimal | Poor | Dead end (unmaintained, X11 only) |
| SPICE | VM only | Yes (in hypervisor) | None | N/A | N/A | Not applicable (VM protocol only) |
| Remmina | Linux only (client) | N/A | N/A | N/A | Moderate | Complementary client (already installed) |
| FreeRDP / xrdp | Client: all; Server: Linux | Yes | None | No (xrdp) | Moderate | Complementary; xrdp Wayland gap |
| WayVNC | Linux (wlroots only) | Yes | None | Yes (wlroots only) | Poor | Niche (Sway users only) |
| DWService | Linux/Mac/Win | No (cloud only) | Yes (cloud relay) | N/A | Good | **Disqualified** (not self-hostable) |
| HopToDesk | Linux/Mac/Win | Partial | Yes | Same as RustDesk | Moderate | No advantage over RustDesk; trust concerns |

### Mesh / Overlay Networking Solutions

| Solution | Self-Hosted | NAT Traversal | Family Onboarding | Device Limit (Free) | Ops Burden | Verdict |
|----------|-------------|---------------|-------------------|---------------------|------------|---------|
| **Tailscale** | Control: No; Relay: Yes | Best-in-class | Easiest (install + sign in) | 100 devices, 3 users | Lowest | **Recommended (ADR-003)** |
| Headscale | Fully | Same as Tailscale | Moderate (custom server URL) | Unlimited | Medium | **Documented fallback** |
| ZeroTier | Partial (licensing change) | Good | Moderate (network ID + approval) | 10 devices (cloud) | Medium | **Secondary fallback** |
| Nebula | Fully | Limited | Poor (cert management) | Unlimited | High | Not recommended (too complex) |
| WireGuard (raw) | Fully | None | Very poor (config files) | Unlimited | Highest | Rejected |
| wg-easy | Hub: Yes | Hub-and-spoke only | Poor (config import) | Unlimited | Medium | Not suitable (not mesh) |
| Firezone | Unsupported | Yes | Moderate | 5 users (cloud) | High | Not recommended (unstable self-host) |
| **NetBird** | Fully | Good | Good (SSO login) | 5 users, 100 peers | Medium-High | Worth monitoring; best full-self-host option |

---

## Recommendations

### Confirmed decisions

1. **RustDesk remains the correct choice for remote desktop** (ADR-001). No evaluated alternative provides a better combination of cross-platform support, self-hosting, NAT traversal, and integrated client+server architecture. MeshCentral is the closest competitor but its server-routed traffic model and macOS issues make it inferior for this use case.

2. **Tailscale remains the recommended network layer** (ADR-003). Its NAT traversal is best-in-class, the free tier is generous, family onboarding is the simplest available, and operational overhead is zero. The SaaS control plane is an acceptable tradeoff for a personal fleet.

### Validated fallback chain

1. **Primary:** Tailscale (free tier) + RustDesk direct IP mode.
2. **First fallback (if Tailscale SaaS becomes unacceptable):** Headscale (self-hosted Tailscale control plane). Same clients, same UX, no device limits. Requires a VPS or home server with a public IP.
3. **Second fallback (if Tailscale client compatibility breaks):** Self-hosted ZeroTier. Different client, different protocol, but true network separation and no device limits. Monitor the v1.16.0 licensing change.
4. **Monitor for future evaluation:** NetBird. The most promising fully-self-hosted option. If it matures further and the Tailscale free tier becomes insufficient, NetBird becomes the primary self-hosted recommendation.

### Tools explicitly not recommended for this fleet

- **Apache Guacamole:** Gateway model, no NAT traversal, heavy infrastructure.
- **Nebula:** Certificate management complexity, poor mobile/family UX, not aimed at hobbyists.
- **WireGuard (raw):** No NAT traversal, manual key management, impractical for non-technical users.
- **Firezone:** Self-hosting explicitly unsupported by maintainers.
- **DWService:** Cloud-only, violates privacy requirement.
- **x11vnc:** Unmaintained, X11-only dead end.
- **HopToDesk:** No advantage over upstream RustDesk, community trust concerns.

---

## Sources

### Remote Desktop
- [RustDesk GitHub](https://github.com/rustdesk/rustdesk)
- [RustDesk Self-Host Documentation](https://rustdesk.com/docs/en/self-host/)
- [RustDesk OSS vs Pro Discussion](https://github.com/rustdesk/rustdesk/discussions/10351)
- [RustDesk Wayland Multi-Monitor (v1.4.3)](https://ubuntuhandbook.org/index.php/2025/10/rustdesk-released-1-4-3-with-multi-monitor-for-wayland-virtual-mouse/)
- [RustDesk macOS Documentation](https://rustdesk.com/docs/en/client/mac/)
- [Tailscale + RustDesk Integration](https://tailscale.com/blog/tailscale-rustdesk-remote-desktop-access)
- [Apache Guacamole 1.6.0 Release](https://guacamole.apache.org/releases/1.6.0/)
- [MeshCentral GitHub](https://github.com/Ylianst/MeshCentral)
- [MeshCentral Agent Documentation](https://ylianst.github.io/MeshCentral/meshcentral/agents/)
- [TurboVNC vs TigerVNC](https://turbovnc.org/About/TigerVNC)
- [VNC Server Comparison (TightVNC, TigerVNC, RealVNC, x11vnc)](https://dohost.us/index.php/2025/11/05/vnc-server-software-comparison-tightvnc-tigervnc-realvnc-x11vnc/)
- [x11vnc GitHub](https://github.com/LibVNC/x11vnc)
- [GNOME Drops X11 Support](https://canartuc.medium.com/gnome-completely-drops-x11-support-the-wayland-era-begins-387e961926c0)
- [SPICE Project](https://www.spice-space.org/)
- [Remmina](https://remmina.org/)
- [FreeRDP](https://www.freerdp.com/)
- [Remote Desktop on Wayland in 2025](https://stackademic.com/blog/remote-desktop-on-wayland-in-2025-what-changed-for-linux-support-engineers)
- [xrdp Wayland Issue](https://github.com/neutrinolabs/xrdp/issues/2629)
- [WayVNC GitHub](https://github.com/any1/wayvnc)
- [WayVNC 0.9 Release](https://www.phoronix.com/news/WayVNC-0.9-Wayland-VNC)
- [DWService](https://www.dwservice.net/en/)
- [HopToDesk vs RustDesk Comparison 2026](https://www.helpwire.app/blog/hoptodesk-vs-rustdesk/)
- [HopToDesk GitLab](https://gitlab.com/hoptodesk/hoptodesk)
- [HopToDesk Fork Discussion](https://github.com/rustdesk/rustdesk/discussions/1590)

### Mesh / Overlay Networking
- [Tailscale Pricing](https://tailscale.com/pricing)
- [Tailscale Free Plan](https://tailscale.com/blog/free-plan)
- [Headscale GitHub](https://github.com/juanfont/headscale)
- [Headscale Documentation](https://docs.headscale.org/)
- [Headscale DERP Configuration](https://headscale.net/stable/ref/derp/)
- [Headscale vs Tailscale Self-Hosting Tradeoff](https://imdmonitor.com/headscale-vs-tailscale-the-self-hosting-trade-off-20251026/)
- [ZeroTier Documentation](https://docs.zerotier.com/)
- [ZeroTier Controller Licensing Change](https://docs.zerotier.com/controller/)
- [ZTNET Private Root Servers](https://ztnet.network/usage/private_root)
- [Nebula GitHub](https://github.com/slackhq/nebula)
- [Nebula Disappointing After 4 Years (Sep 2025)](https://blog.ewonchang.com/2025/09/27/nebula-mesh-vpn-still-disappointing-after-4-years/)
- [Nebula Introduction](https://nebula.defined.net/docs/)
- [wg-easy GitHub](https://github.com/wg-easy/wg-easy)
- [Firezone GitHub](https://github.com/firezone/firezone)
- [NetBird GitHub](https://github.com/netbirdio/netbird)
- [NetBird Documentation](https://docs.netbird.io/)
- [NetBird Architecture (Feb 2026)](https://dasroot.net/posts/2026/02/netbird-architecture-wireguard-go-zero-trust/)
- [NetBird vs Tailscale Comparison](https://wz-it.com/en/blog/netbird-vs-tailscale-comparison/)
- [Top Open Source Tailscale Alternatives 2026](https://pinggy.io/blog/top_open_source_tailscale_alternatives/)
