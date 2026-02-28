# MVP Epic Proposal

**Supporting doc for:** [VISION-001](./(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)
**Created:** 2026-02-28
**Based on:** [mvp-open-questions.md](./mvp-open-questions.md) answers

---

## What changed

Your Q&A answers reshape the architecture in several ways:

- **Single repo.** No fleet-agent split. The bootstrap is idempotent — it
  detects what the machine needs and acts accordingly.
- **VPS is the consolidated hub.** WireGuard + CoreDNS + Guacamole + SSH
  relay, all fungible. Destroy and rebuild from repo state.
- **Nodes are autonomous agents.** They poll the git repo for topology
  changes, decrypt with SOPS/age, and self-configure. Initial onboarding
  uses Magic Wormhole for key transfer.
- **TUI replaces web UI.** A textual app the operator can run over SSH (or
  that a family member could run locally when the tunnel is down).
- **SSH mesh is first-class.** `ssh mom.wg` from any node, routed via hub,
  no per-session forwarding config.
- **DNS is cross-cutting.** Not its own epic — it's woven into hub (CoreDNS
  server), provisioning (zone rendering), and node agent (client DNS config).

## What happens to current epics

| Current | Disposition | Rationale |
|---------|-------------|-----------|
| EPIC-001 (Remote Fleet Management) | **Abandon** | Umbrella epic from a pre-merge world. The vision + new epics cover this scope. |
| EPIC-002 (Provisioning CLI) | **Absorb** into new Hub + Node Agent epics | `wgmesh` CLI concept lives on, but "provisioning" splits: hub-side sync goes to Hub Bootstrap, node-side provisioning goes to Node Agent |
| EPIC-003 (Client Web UI) | **Absorb** into Node Agent | Web UI → TUI. Same purpose (local status + troubleshooting), different medium |
| EPIC-004 (Operator Dashboard) | **Re-scope** as Tunnel Monitoring | Narrowed to WireGuard health. Guacamole handles connection management |
| EPIC-005 (VPS Bootstrap) | **Evolve** into Hub Bootstrap | Expands to include Guacamole, SSH relay, and consolidated hub concept |
| EPIC-006 (Internal DNS) | **Distribute** across Hub + Node Agent | CoreDNS setup → Hub. Zone rendering → Hub. Client DNS config → Node Agent. No standalone epic |

## Proposed new epics

### EPIC-007: Hub Bootstrap & Disaster Recovery

*Evolved from EPIC-005. Absorbs EPIC-006 (DNS server side) and Guacamole deployment.*

The VPS is a single fungible hub. One command rebuilds it from scratch. It
runs:

- **WireGuard relay** — hub-and-spoke, all inter-node traffic routes through
- **CoreDNS** — `.wg` zone auto-generated from network state
- **Guacamole** — browser-based RDP/VNC/SSH gateway to all nodes
- **SSH relay** — ProxyJump target so any node can SSH to any other
- **Status endpoint** — JSON status for monitoring

**Key properties:**
- Fully rebuildable from repo state in <10 minutes
- Idempotent — safe to re-run
- Guacamole config (connections, users) generated from network state, not
  manually configured
- No state lives only on the VPS — everything is in the repo

**Success criteria:**
- `wgmesh hub deploy` against a fresh Ubuntu VPS installs and configures
  everything
- Destroying the VPS and redeploying to a new one restores full
  functionality
- All services start automatically on boot
- Guacamole connections are auto-generated from peer list (no manual
  connection setup per machine)

---

### EPIC-008: Node Agent

*New. Absorbs parts of EPIC-002 (node-side provisioning), EPIC-003 (client
UI), and EPIC-006 (DNS client side).*

A long-running agent on every fleet node. Handles its own onboarding,
keeps its topology in sync, manages WireGuard, enables the right access
protocols, and gives the operator a TUI for troubleshooting.

**Onboarding (first run):**
- Operator runs `wgmesh add <name>` on their workstation → generates config
- Config transferred to new node via Magic Wormhole (operator sends, node
  receives — one short code, works over any network)
- Agent installs WireGuard, applies config, connects to hub

**Steady state:**
- Polls git repo for topology changes (new peers, removed peers, config
  updates)
- Decrypts relevant portions with SOPS/age
- Applies WireGuard config updates (hot-reload, no tunnel restart unless
  necessary)
- Enables native remote access protocols based on machine role:
  - Servers: sshd only
  - Linux workstations: sshd + xrdp (or VNC)
  - macOS workstations: Remote Login + Screen Sharing
  - Windows workstations: RDP + OpenSSH server
- Generates SSH config (`~/.ssh/config.d/wgmesh`) with ProxyJump entries for
  all peers → enables `ssh mom.wg` from any node
- Configures DNS client (sets WireGuard DNS to hub IP)

**TUI:**
- Textual (Python) or similar terminal UI framework
- Shows: tunnel status, assigned IP, DNS name, last handshake, transfer
  stats, peer list with reachability
- Actions: restart tunnel, force topology sync, show logs
- Runnable over SSH — operator can SSH in via side-channel and diagnose
- Also runnable locally by a family member if guided by the operator

**Success criteria:**
- New node onboarded in <5 minutes (from `wgmesh add` to connected tunnel)
- Topology changes propagate to all nodes within polling interval (e.g., 5
  min)
- TUI shows accurate tunnel status on all three platforms
- Native remote access protocol enabled automatically based on detected role
- `ssh <peer>.wg` works from any onboarded node

---

### EPIC-009: Tunnel Monitoring

*Re-scoped from EPIC-004. Narrowed to WireGuard health only.*

Give the operator visibility into WireGuard tunnel health across the fleet.
Guacamole handles desktop/SSH connection management — this covers the
network layer underneath.

**What it shows:**
- All peers: name, IP, last handshake time, transfer RX/TX, endpoint
- Status indicators: connected (handshake <2 min), stale (2-5 min), offline
  (>5 min)
- Runs on the VPS (accessible via Guacamole or direct browser)

**Implementation options** (to be decided during speccing):
- A. Status page generated by a cron script (static HTML from `wg show`)
- B. Lightweight web app (e.g., Flask) with on-demand refresh
- C. TUI subcommand in the node agent (`wgmesh monitor`)
- D. Guacamole extension or custom dashboard panel

**Success criteria:**
- Operator can see the WireGuard disposition of all machines from a single
  view
- No persistent daemon required beyond what already runs on the VPS
- Data is current within 1 minute of request

---

## Dependency graph

```
EPIC-007 (Hub Bootstrap)
  ↑
  ├── EPIC-008 (Node Agent) — needs hub running to connect
  │     ↑
  │     └── EPIC-009 (Tunnel Monitoring) — needs nodes connected to monitor
  │
  └── wgmesh CLI — shared tooling between hub deploy and node provisioning
```

The `wgmesh` CLI is not its own epic — it's the shared tool that both
EPIC-007 and EPIC-008 use. The hub-facing commands (`hub deploy`, `hub
sync`) belong to EPIC-007. The node-facing commands (`add`, `remove`,
`list`, `status`) belong to EPIC-008.

## MVP vs post-MVP

| Epic | MVP? | Rationale |
|------|------|-----------|
| EPIC-007 (Hub Bootstrap) | **Yes** | Nothing works without the hub |
| EPIC-008 (Node Agent) | **Yes** | Nothing works without nodes on the network |
| EPIC-009 (Tunnel Monitoring) | **No** | Operator can `wg show` via SSH. Nice-to-have |

Within EPIC-008, the TUI and git-polling features could be deferred to a
post-MVP "hardening" phase if needed. The MVP path for node agent might be:

1. `wgmesh add` + Magic Wormhole transfer + manual WireGuard install/config
2. SSH config generation
3. Native protocol enablement

Then layer on git-polling, TUI, and auto-updates as EPIC-008 matures.

---

## Open questions for this proposal

1. **Numbering:** Start at EPIC-007 to preserve lineage with abandoned
   001-006? Or renumber from EPIC-001 (clean slate, old epics are historical
   record)?

2. **`wgmesh` as a single binary?** Should the CLI, node agent, and TUI be
   one binary invoked in different modes (`wgmesh hub deploy`, `wgmesh agent
   run`, `wgmesh tui`)? Or separate packages?

3. **Git polling model:** How does the node agent authenticate to the git
   repo? The repo contains SOPS-encrypted secrets — the node needs the age
   key to decrypt its own config. Does the node get a read-only deploy key?
   Does it clone the whole repo or fetch just the state file?

4. **Magic Wormhole dependency:** Is Magic Wormhole acceptable as an
   onboarding dependency? It requires `wormhole` installed on both the
   operator's machine and the target node. Alternative: generate a
   self-contained script/archive the operator can `scp` or share via any
   file transfer method.
