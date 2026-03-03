# Porthole — Branding & Style Guide

Supporting document for VISION-001: Remote Access for a Personal Fleet.

---

## Project name

**Porthole**

The project is called **Porthole**. It is not called "wgmesh", "wg-mesh",
"remote-fleet", or any other name derived from its component tools.

The name is lowercase when used as a command, package, or URL slug: `porthole`.
It is title-case in prose: Porthole.

---

## What Porthole is

Porthole is an infrastructure bootstrap that turns any Linux, macOS, or Windows
machine into a node in a private, always-on remote-access network. Run the
bootstrap on a machine and it becomes reachable — via SSH, remote desktop, or
both — from every other node in the fleet.

One sentence: **Private remote access for a personal fleet of machines.**

---

## What Porthole is not

| Wrong framing | Why | Right framing |
|---------------|-----|---------------|
| "a mesh network" | The network is hub-and-spoke, not a full mesh. All traffic relays through a VPS hub. | "a hub-and-spoke remote-access network" |
| "a VPN" | WireGuard is the transport layer, not the product. The product is remote access. | "remote access over WireGuard" |
| "wgmesh" | `wgmesh` is the CLI tool, not the project. | "Porthole" (project), `wgmesh` (CLI command) |
| "a mesh VPN" | Same as above — there is no full mesh. | "a hub-and-spoke relay" |

---

## Architecture terminology

Use these terms consistently in docs, code comments, and user-facing output.

| Concept | Preferred term | Avoid |
|---------|----------------|-------|
| The overall system | Porthole | wgmesh, remote-fleet |
| The VPS running WireGuard + Guacamole + CoreDNS | **hub** | server, master, gateway |
| Any non-hub machine in the fleet | **node** or **peer** | client, slave, endpoint |
| The network topology | **hub-and-spoke** | mesh, full mesh, p2p |
| The WireGuard interface on the hub | **wg0** | (don't abstract this) |
| The WireGuard interface on a node | **wg0** | (same) |
| The management CLI | `wgmesh` | porthole (the CLI command is `wgmesh`) |
| The encrypted state file | `network.sops.yaml` | config file, state |
| The reverse SSH tunnel | **tunnel** | reverse proxy, backdoor |
| The watchdog process | **watchdog** | health-check, monitor |

---

## Component inventory

Porthole is composed of best-of-breed components. Name them correctly.

| Component | What it does in Porthole | Correct name |
|-----------|--------------------------|--------------|
| WireGuard | Transport layer for hub-and-spoke connectivity | WireGuard |
| CoreDNS | Resolves `<node>.wg` hostnames inside the fleet | CoreDNS |
| nftables | Network isolation on the hub | nftables |
| Apache Guacamole | Browser-based remote desktop gateway | Guacamole |
| Caddy | TLS termination in front of Guacamole | Caddy |
| SOPS + age | Encrypted state file at rest | SOPS / age |

Do not use trademarked names as verbs: say "connect via WireGuard," not "WireGuard the node."

---

## Node roles

| Role | Label in CLI | What it gets |
|------|-------------|--------------|
| Headless server | `server` | WireGuard + SSH |
| Workstation (operator or family) | `workstation` | WireGuard + SSH + Guacamole remote desktop |
| Family member's machine | `family` | WireGuard + SSH (passive; no operator interaction after setup) |

---

## Writing style

- **Direct and technical.** The audience is a single technical operator. Skip marketing hedges.
- **Imperative for instructions.** "Run `wgmesh bootstrap`", not "You can run `wgmesh bootstrap`".
- **Short sentences.** Each sentence should make one point.
- **Nautical theme: light touch.** The name is nautical; the docs are not a theme park. One or two nautical metaphors across the whole README is enough. Do not force them.
- **No "mesh".** Every occurrence of "mesh" referring to the network topology should be replaced with "hub-and-spoke" or simply removed.

---

## Hostname convention

Fleet nodes are reachable at `<name>.wg` within the fleet (resolved by CoreDNS).
Examples: `alice.wg`, `homelab.wg`, `hub.wg`.

The hub is always `hub.wg` on the internal network and its public endpoint is
whatever the operator configured at `wgmesh init --endpoint`.

---

## CLI vs. project name

The management CLI command is **`wgmesh`**. This is a historical artifact — the
command was named before the project was. Do not rename the CLI to avoid churn.

When referring to the project in prose, use **Porthole**.
When referring to the command a user types, use **`wgmesh`**.

> Run `wgmesh add alice --role workstation` to register a new node in Porthole.
