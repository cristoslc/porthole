# WireGuard Mesh Relay Network — Architecture Overview

**Supporting doc for:** [VISION-001](./(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)
**Last updated:** 2026-02-28

---

## Summary

A single Git repository defines an entire WireGuard relay network — every peer, every key, every DNS name — encrypted at rest with SOPS/age and deployable to a fresh VPS with one command. Family members never think about it. The operator provisions a peer once, pushes config, and forgets. When the VPS dies, clone the repo and rebuild in minutes. No SaaS dependency, no licensing changes, no surprise pricing tiers.

## Architecture

All inter-peer traffic routes through a VPS relay hub running WireGuard and CoreDNS. This is a hub-and-spoke model — not automatic direct peer-to-peer hole-punching. The tradeoff is simplicity and reliability over latency: every connection works regardless of NAT topology because it always goes through the VPS.

### Components

| Component | Role | Runs on |
|-----------|------|---------|
| `porthole` CLI | Provisioning, state management, deployment | Operator's workstation |
| WireGuard hub | Relay all inter-peer traffic | VPS |
| CoreDNS | Internal `.wg` DNS resolution | VPS |
| Status script | On-demand peer status as JSON | VPS |
| Client web UI | Local tunnel health display | Each client node |
| Operator dashboard | Network-wide status view | Operator's homelab |

### State management

The network's source of truth is `network.sops.yaml` — a SOPS-encrypted YAML file in the Git repo containing all peer definitions, key pairs, IP assignments, and DNS names. All configs (WireGuard, CoreDNS zone) are rendered from this file via Jinja2 templates. Private keys are encrypted with age; public metadata may be cleartext.

## Success metrics

- Time to provision a new peer: under 2 minutes from CLI command to connected tunnel.
- Time to rebuild from scratch on a new VPS: under 10 minutes.
- Zero-touch operation for non-operator peers after initial provisioning.
- All WireGuard private keys encrypted in the repository; no secrets in plaintext at rest outside of deployed machines.

## Runtime model

All agents on client nodes — WireGuard, native remote desktop services (xrdp on Linux, Screen Sharing on macOS, RDP on Windows), and the status web UI — run as background services (systemd units on Linux, launchd daemons on macOS, Windows services). Guacamole on the hub provides browser-based gateway access to these native protocols. No foreground application window or tray icon is required to maintain connectivity. The system is invisible to non-operator users during normal operation.

## Non-goals

- Not a general-purpose SD-WAN or enterprise networking product.
- Does not aim to replace Tailscale/ZeroTier for users who prefer managed services.
- Does not provide automatic direct peer-to-peer hole-punching — all inter-peer traffic routes through the VPS relay.
- Does not include a multi-tenant or multi-operator access model.
