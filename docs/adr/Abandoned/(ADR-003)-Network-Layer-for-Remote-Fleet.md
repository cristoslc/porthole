# ADR-003: Network Layer for Remote Fleet

**Status:** Abandoned
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Epic:** [(EPIC-001) Remote Fleet Management](../../epic/Proposed/(EPIC-001)-Remote-Fleet-Management/(EPIC-001)-Remote-Fleet-Management.md)
**Affects:** [PRD-004](../../prd/Abandoned/(PRD-004)-RustDesk-Self-Hosted-Relay/(PRD-004)-RustDesk-Self-Hosted-Relay.md) (Abandoned)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 9b4365e | Initial creation |
| Abandoned | 2026-02-28 | d69e12e | Recommendation (Tailscale ACLs) not adopted; superseded by ADR-004 (WireGuard hub-and-spoke) |

---

## Context

The fleet consists of ~10 machines across three platforms:

- **6-7 home machines** (workstations, a Proxmox host, possibly NAS) — most
  already on a Tailscale tailnet alongside VMs and Docker containers.
  A mix of Linux, macOS, and Windows.
- **2+ remote family machines** — not currently on any shared network. Managed
  occasionally via remote desktop or SSH. Operated by non-technical family
  members. Likely Windows.

**Platform constraint:** This repo's Ansible automation targets Linux and
macOS only. Windows machines in the fleet are not provisioned by `make apply`
— their network agent (Tailscale, ZeroTier, or WireGuard) and RustDesk must
be installed and configured manually or via a separate mechanism. The chosen
network layer must have a native Windows client with a straightforward manual
setup path. All options evaluated below (Tailscale, ZeroTier, WireGuard,
RustDesk) have native Windows clients.

PRD-002 installed RustDesk on managed workstations. PRD-004 proposed a
self-hosted RustDesk relay server. During PRD-004 review, two questions
surfaced:

1. **Is a relay needed at all?** If all machines are on a mesh VPN, RustDesk
   can connect via direct IP — no relay, no rendezvous server, no public
   infrastructure dependency.
2. **What network layer should carry the traffic?** The existing Tailscale
   tailnet has VMs and Docker containers on it. Adding family machines and
   RustDesk traffic to the same flat network raises isolation concerns.

This ADR decides the network layer for remote fleet connectivity.

## Decision drivers

- **Isolation:** RustDesk-only machines (especially family machines) should not
  be able to reach infrastructure services (VMs, Docker, NAS).
- **Family onboarding friction:** Remote family members are non-technical.
  Setup must be as simple as possible — ideally "install one app, done."
- **Operational overhead:** This is a personal fleet, not a business. The
  solution must be low-maintenance.
- **Cost:** Free or near-free strongly preferred.
- **Self-hosting posture:** Prefer self-hosted where the operational burden is
  proportional to the benefit. Accept SaaS where self-hosting adds significant
  complexity for marginal gain.
- **No third-party relay dependency:** Session traffic (signaling, relay,
  data) should not pass through infrastructure we don't control.

## Options considered

### Option A: Tailscale ACL segmentation (existing tailnet)

Use the existing Tailscale tailnet. Add family machines to it. Use ACL tags
to isolate RustDesk machines from infrastructure.

**How it works:**

- Tag RustDesk machines as `tag:rustdesk`, infrastructure as `tag:infra`.
- ACL rules: `tag:rustdesk` can reach `tag:rustdesk` on RustDesk ports
  (21710-21719) + SSH (22) only. `tag:rustdesk` cannot reach `tag:infra`.
- Family machines (including Windows) join the tailnet via pre-auth key
  (one-time, expires after use). Family member installs Tailscale, pastes
  key, done. Tailscale has native clients for Windows, macOS, and Linux —
  the Windows installer is a standard MSI with a GUI login flow.
- RustDesk connects via Tailscale IPs (100.x.y.z). No relay server needed.
- Windows machines: Tailscale and RustDesk both installed manually (MSI
  installers). Configuration is the same — set Tailscale IP as the RustDesk
  connection target.

**Tailscale plan considerations:**

The existing tailnet is on the Personal free plan (3 users, 100 devices).
Current device count includes VMs and Docker containers. Each node running
`tailscaled` counts as one device — this includes every VM and every Docker
container with Tailscale inside it.

| Plan | Users | Devices | Cost | ACL capability |
|------|-------|---------|------|----------------|
| Personal | 3 | 100 | Free | Tag-based ACLs work. Named-user ACLs limited to autogroups. |
| Personal Plus | 6 | 100 | $5/mo | Same ACL capability. More users for family sharing. |
| Starter | Unlimited | 100 + 10/user | $6/user/mo | Autogroup ACLs only. |
| Premium | Unlimited | 100 + 20/user | $18/user/mo | Full named-user + custom group ACLs. |

**Device count optimization:** Instead of giving each Docker container its own
Tailscale node, run one subnet router per Docker host. The router exposes the
Docker bridge network and counts as 1 device instead of N.

**Multi-tailnet is not viable:** Tailscale's multiple-tailnets feature
(alpha, Oct 2025) requires contacting sales, mandates same domain/IdP, and
targets enterprise use. A device can only be in one tailnet at a time.
Creating a second tailnet under a separate account is possible but means
account-switching on admin machines — impractical for daily use.

| Pros | Cons |
|------|------|
| Zero additional infrastructure | Family machines land on the same tailnet as all other devices |
| Free tier likely sufficient (100 devices) | ACL misconfiguration could expose infrastructure |
| Tailscale handles NAT traversal, DERP relay, key rotation automatically | Tag-based ACLs are policy isolation, not cryptographic separation |
| Family onboarding: install app + paste pre-auth key | If device count grows (many VMs/containers), may hit 100-device limit |
| MagicDNS for human-readable hostnames | RustDesk does not resolve MagicDNS names — must use raw IPs (100.x.y.z) |
| Already in use — no new tool to learn | Third-party SaaS control plane dependency for device registration |

### Option B: Separate ZeroTier network (self-hosted controller)

Create a dedicated ZeroTier network for RustDesk traffic, completely separate
from the existing Tailscale tailnet. Run a self-hosted ZeroTier controller
to avoid device limits.

**How it works:**

- Deploy `zerotier-one` + a web UI (ztncui or zero-ui) on Proxmox or a VPS.
- Create a ZeroTier network for RustDesk fleet.
- Each managed machine joins the ZeroTier network. Machines already on
  Tailscale stay on Tailscale too — ZeroTier and Tailscale coexist
  independently (a device can be in both simultaneously).
- RustDesk connects via ZeroTier IPs. No relay server needed.
- Family machines install ZeroTier, join the network ID, get approved via
  the web UI.

**ZeroTier cloud pricing (new accounts, post Nov 2025):**

| Plan | Devices | Networks | Cost |
|------|---------|----------|------|
| Personal | 10 | 1 | Free |
| Essential | 10+ | 10 | $18/mo + $2/device beyond 10 |
| Scale | 100+ | Unlimited | $179/mo + $1.80/device beyond 100 |

The free tier (10 devices, 1 network) is borderline for ~12 machines. A
self-hosted controller has **no device limits** — the cloud pricing only
applies to ZeroTier Central (their SaaS).

| Pros | Cons |
|------|------|
| True network separation — cryptographically distinct from Tailscale | New tool to learn, deploy, and maintain |
| Self-hosted controller: no device limits, no SaaS dependency | Self-hosted controller is another service to keep running |
| Devices can be in both ZeroTier and Tailscale simultaneously | ZeroTier cloud free tier is only 10 devices (tight for 12 machines) |
| Layer 2 support (broadcast, mDNS) — useful for service discovery | Custom protocol (not WireGuard) — smaller ecosystem |
| Full control over network policies via Flow Rules | Flow Rules language is less intuitive than Tailscale ACLs |
| Web UI for approving/managing devices | Family onboarding: install ZeroTier + enter network ID + wait for approval (slightly more steps) |

### Option C: WireGuard hub-and-spoke (fully self-hosted)

Run a WireGuard VPN hub on Proxmox or a VPS. All fleet machines connect as
spokes. The hub routes traffic between spokes.

**How it works:**

- Generate a WireGuard keypair for the hub and each spoke.
- Hub runs on a machine with a stable IP (Proxmox host, VPS).
- Each spoke gets a `.conf` file with the hub's endpoint and public key.
- IP forwarding on the hub enables spoke-to-spoke routing.
- RustDesk connects via WireGuard tunnel IPs (e.g., 10.0.0.x).

| Pros | Cons |
|------|------|
| Fully self-hosted, zero third-party dependency | Highest setup complexity: keypair generation, config distribution, IP allocation |
| WireGuard is in-kernel, battle-tested, very fast | No automatic NAT traversal — hub must be publicly reachable |
| Zero cost (no SaaS, no license) | Manual key rotation — error-prone at scale |
| Lowest attack surface (no control plane daemon) | Family onboarding: must install WireGuard + import config file (technically assisted handoff) |
| | No MagicDNS, no device management UI, no health monitoring |
| | Adding/removing machines requires hub config edit + spoke config distribution |
| | Hub is a SPOF — if it goes down, no spoke-to-spoke connectivity |

**Simplification tools:** wg-easy (Docker, web UI for peer management) or
Headscale (self-hosted Tailscale control plane, uses official Tailscale
clients) can reduce operational burden. Headscale is essentially "self-hosted
Tailscale" — same client UX, you run the coordination server.

### Option D: RustDesk Server Pro ($9.90/mo)

Use RustDesk's own commercial server as the sole network+remote-desktop layer.
No separate VPN needed for RustDesk sessions.

**How it works:**

- Deploy RustDesk Server Pro on Proxmox or a VPS.
- All machines connect to the Pro server for rendezvous, relay, and
  management.
- Pro provides: address book with online/offline status, device groups,
  centralized settings push, connection audit logs, web console.
- NAT traversal (hole-punching + relay fallback) is handled by RustDesk
  itself.

**What Pro does NOT provide:**

- No general-purpose VPN or SSH access — it only handles the RustDesk
  protocol.
- No network-layer connectivity between machines.
- If you also need SSH, you still need a VPN layer alongside Pro.

| Plan | Users | Devices | Cost |
|------|-------|---------|------|
| Individual | 1 | 20 | $9.90/mo ($119/yr) |
| Basic | 10 | 100 | $19.90/mo ($239/yr) |

| Pros | Cons |
|------|------|
| Address book with peer online/offline status | $119/yr ongoing cost for a personal fleet |
| Centralized device management and settings push | Does NOT provide SSH or general network access — still need a VPN for that |
| Connection audit logs | Adds a paid dependency to the stack |
| Web console for administration | Self-hosted Pro still requires your own server |
| Custom branded client builds (Basic+) | OSS RustDesk + a VPN achieves the same connectivity for free |
| OIDC/SSO support (Basic+) | Overkill for 1-user fleet — OIDC and multi-user features are unused |

### Option E: Tailscale + self-hosted RustDesk OSS relay (PRD-004 as-is)

Keep the existing Tailscale tailnet, add family machines, and also deploy a
self-hosted RustDesk relay (hbbs+hbbr) for signaling/peer-discovery.

This is what PRD-004 currently proposes. The relay provides RustDesk-native
peer discovery and status, while Tailscale provides the network transport.

| Pros | Cons |
|------|------|
| RustDesk peer discovery and 9-digit IDs work | Two overlapping systems: Tailscale for connectivity + RustDesk relay for signaling |
| Online/offline status in RustDesk UI | Relay is largely redundant — Tailscale already provides the tunnel |
| Familiar RustDesk UX (no IP addresses to remember) | Additional service to deploy and maintain |
| | Does not solve the isolation problem without Tailscale ACLs |

---

## Analysis

### The SSH question narrows the field

Options D (RustDesk Pro) and E (Tailscale + OSS relay) are incomplete if SSH
access to family machines is also a goal. RustDesk handles remote desktop only
— it does not provide network-layer connectivity. If SSH is in scope, a VPN
layer is mandatory regardless of what RustDesk configuration is chosen.

This means the core decision is between Options A, B, and C for the network
layer. RustDesk then operates *on top of* that layer via direct IP connections,
and the self-hosted relay (PRD-004) becomes unnecessary.

### Isolation vs. simplicity tradeoff

| | Isolation model | Family onboarding | Ops burden |
|-|----------------|-------------------|------------|
| **A. Tailscale ACLs** | Policy (ACL tags) — same tailnet, logically separated | Easiest: install app + pre-auth key | Lowest |
| **B. ZeroTier self-hosted** | Cryptographic — completely separate network | Moderate: install app + network ID + admin approval | Medium — another service to run |
| **C. WireGuard hub** | Cryptographic — completely separate network | Hardest: install app + import config file | Highest — manual key/config management |

### Cost comparison (annual)

| Option | Infrastructure cost | License cost | Total |
|--------|-------------------|--------------|-------|
| A. Tailscale ACLs | $0 (free tier) | $0 | $0 |
| A. Tailscale ACLs (Personal Plus) | $0 | $60/yr | $60/yr |
| B. ZeroTier self-hosted | $0 (on Proxmox) | $0 | $0 |
| B. ZeroTier cloud Essential | — | $216+/yr | $216+/yr |
| C. WireGuard hub (home) | $0 | $0 | $0 |
| C. WireGuard hub (VPS) | $36-72/yr | $0 | $36-72/yr |
| D. RustDesk Pro + VPN | VPN cost + | $119/yr | $119+/yr |

---

## Recommendation

**Option A (Tailscale ACL segmentation)** is the recommended decision, with
Option B (self-hosted ZeroTier) as the documented fallback if Tailscale
becomes unacceptable.

**Rationale:**

1. **Tailscale is already deployed.** Adding machines and ACL tags is
   incremental work, not a new system.
2. **Family onboarding is the critical path.** Non-technical family members
   need the lowest possible friction. Tailscale's "install app, paste key"
   flow is the simplest option. ZeroTier's "install app, enter network ID,
   wait for approval" is close but adds a step. WireGuard config-file
   distribution is a dealbreaker for non-technical users.
3. **ACL isolation is sufficient for a personal fleet.** The threat model is
   "family member's compromised machine shouldn't be able to reach my NAS" —
   not "nation-state attacker on the tailnet." Tag-based ACLs provide this.
4. **Zero cost, zero new infrastructure.** No VPS, no controller to run, no
   new service to monitor.
5. **SSH works natively.** Tailscale SSH (`tailscale ssh hostname`) eliminates
   SSH key management entirely.
6. **Escape hatch exists.** If Tailscale's SaaS dependency becomes
   unacceptable, Headscale provides a self-hosted control plane compatible
   with the same Tailscale clients — no client-side changes needed.

**Consequences for PRD-004:** The self-hosted RustDesk relay (hbbs+hbbr) is
**not needed** under this decision. All machines are on the same Tailscale mesh
and RustDesk connects via Tailscale IPs. PRD-004 should be moved to
**Abandoned** with a note that the mesh VPN eliminates the relay requirement.

**Consequences for RustDesk configuration:** The `remote-desktop` Ansible role
should be updated to:

- Configure RustDesk with an empty ID Server and Relay Server (disabling
  public server contact).
- Document that connections use Tailscale IPs (100.x.y.z) rather than
  RustDesk 9-digit IDs.
- Accept the tradeoff: no online/offline peer status in RustDesk's UI.
  `tailscale status` provides this at the network layer instead.

**Consequences for repo architecture:** The fleet agent (Tailscale + RustDesk
install and configuration) should likely live in a **separate repo** from the
workstation bootstrapper. Rationale:

- Not every target machine is a personal dev workstation. Family machines,
  lightweight non-coding boxes, and home servers need the network/remote-desktop
  layer without the full workstation stack (dev tools, dotfiles, editors, etc.).
- Windows is a first-class target for the fleet agent but not for the
  workstation bootstrapper.
- A separate repo can be run independently on any machine, or consumed as a
  dependency by the workstation repo.

The integration model (Ansible Galaxy role, git submodule, or standalone repo
with loose coupling) is a separate decision — to be resolved in a follow-up
ADR or spike before the provisioning PRD is written.

**Consequences for Tailscale provisioning:** A new PRD (in the fleet-agent
repo, once the repo boundary is decided) is needed to:

- Install and configure Tailscale on Linux, macOS, and Windows.
- Define the ACL tag schema (`tag:rustdesk`, `tag:infra`, etc.).
- Define the pre-auth key workflow for family machine onboarding.
- Optimize device count (subnet routers for Docker hosts instead of
  per-container Tailscale).
- Monitor device count against the 100-device limit.
- Install and configure RustDesk to use Tailscale IPs (cross-platform).
- Provide documented manual setup procedures for Windows.

---

## Alternatives considered

### ZeroTier (Option B) — Not rejected, documented as fallback

ZeroTier is a strong alternative. The self-hosted controller provides true
network separation and unlimited devices. It was not selected as the primary
recommendation because:

- It adds a new tool and a new service to maintain.
- Family onboarding is slightly more complex.
- The incremental isolation benefit over Tailscale ACLs does not justify the
  operational cost for a personal fleet.

If Tailscale's free tier becomes insufficient (device limits), their pricing
becomes unacceptable, or their SaaS reliability degrades, self-hosted ZeroTier
is the documented pivot.

### WireGuard hub-and-spoke (Option C) — Rejected

Maximum sovereignty but maximum operational burden. Manual key generation,
config distribution, and the lack of automatic NAT traversal make this
impractical for family machines operated by non-technical users. The existence
of Headscale (self-hosted Tailscale control plane) makes raw WireGuard
hub-and-spoke unnecessary — Headscale provides the same self-hosting benefit
with dramatically less operational friction.

### RustDesk Server Pro (Option D) — Rejected

Adds cost ($119/yr) without solving the SSH/network-access requirement. The
address book, device management, and audit logs are nice-to-haves but not
worth paying for when a VPN + RustDesk OSS achieves the same connectivity.
Would be reconsidered if the fleet grows beyond ~20 machines or if multi-user
access control becomes a requirement.

### Tailscale + RustDesk relay (Option E) — Rejected

Running a self-hosted RustDesk relay alongside Tailscale is redundant. The
relay's value (peer discovery, NAT traversal, fallback transport) is entirely
subsumed by Tailscale. The only loss is RustDesk's 9-digit ID system and
in-app peer status — acceptable tradeoffs.
