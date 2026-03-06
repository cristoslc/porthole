---
artifact: EPIC-006
title: Homelab Service Exposure
status: Abandoned
author: cristos
created: 2026-02-28
last-updated: 2026-03-03
parent-vision: VISION-001
depends-on:
  - EPIC-001
  - EPIC-005
success-criteria:
  - Services reachable by <name>.home.example.com from LAN, Tailscale, and internet contexts
  - Valid TLS in all contexts via single wildcard cert issued with DNS-01
  - Local DNS resolver returns LAN IPs for private-zone queries; forwards else upstream
  - Tailscale split DNS routes home.example.com queries to local resolver
  - VPS performs SNI pass-through to homelab reverse proxy via WireGuard
  - Internet exposure is opt-in per service (public DNS record + VPS SNI route)
---

# EPIC-006: Homelab Service Exposure

**Status:** Abandoned
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-03-02
**Parent Vision:** [VISION-001](../../../vision/Active/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Proposed | 2026-02-28 | 6405885 | Initial creation, merged from external project |
| Abandoned | 2026-03-03 | ce2fa6a | Out of scope for fleet remote access; belongs in a dedicated homelab-infra repo |

---

## Purpose

Design the service-exposure architecture for the homelab: how services are made accessible across three network contexts (LAN, Tailscale, internet), with DNS names and valid TLS in all cases.

## Constraints

- **Cloudflare Tunnel:** unacceptable
- **Tailscale MagicDNS:** acceptable as fallback only, not primary
- **Internet relay:** WireGuard tunnel via private relay VPS (already exists)
- **DNS upstream:** NextDNS or Control-D (privacy/filtering)

## Findings

1. **NextDNS / Control-D cannot do split-horizon DNS.** Both are cloud resolvers. They support per-profile rewrites but not source-context-aware resolution. They cannot return different IPs for LAN vs Tailscale vs internet clients because all queries appear from the same public egress IP. Role: upstream forwarder only, not authoritative for private zones.

2. **A local DNS resolver is required.** AdGuard Home or Technitium handles the private zone (`home.example.com`) authoritatively, returning LAN IPs. Forwards all other queries upstream to NextDNS/Control-D. Must listen on both the LAN IP and the Tailscale IP (`100.104.71.107`).

3. **Tailscale subnet routing collapses LAN and Tailscale into one case.** Homelab node advertises the LAN CIDR to the Tailscale mesh. Remote Tailscale clients route to LAN IPs through the homelab node transparently. Result: DNS returns `192.168.x.x` for both LAN and Tailscale clients — no separate Tailscale-IP rewrites needed. Tailscale split DNS (admin console) points `home.example.com` to the local resolver at `100.104.71.107`.

4. **DNS-01 challenge is the only viable TLS strategy.** HTTP-01 fails for LAN/Tailscale-only services. DNS-01 works entirely out-of-band. A wildcard cert (`*.home.example.com`) via Cloudflare DNS-01 covers all contexts with a single cert renewed centrally.

5. **VPS relay should do SNI pass-through, not TLS termination.** VPS reads SNI header, forwards TCP stream to homelab via WireGuard. Wildcard cert lives only on the homelab reverse proxy. Avoids dual cert management. WireGuard provides transport encryption; TLS is end-to-end from client to homelab.

## Architecture

### Traffic flow

```
Internet client  → VPS public IP (SNI TCP passthrough)
                   → WireGuard tunnel → Homelab reverse proxy

Tailscale client → Tailscale mesh
                   → subnet route (LAN CIDR advertised by homelab node)
                   → Homelab reverse proxy (via LAN IP)

LAN client       → LAN → Homelab reverse proxy
```

### DNS resolution

| Client | Resolver | Answer |
|--------|----------|--------|
| LAN | Local resolver (AdGuard/Technitium) | `192.168.x.x` |
| Tailscale (remote) | Tailscale split DNS → local resolver at `100.104.71.107` | `192.168.x.x` (subnet-routed) |
| Internet | Public DNS (Cloudflare authoritative) | VPS public IP (opt-in per service) |

### TLS

Single wildcard `*.home.example.com` via DNS-01. Issued and renewed on homelab. Presented by homelab reverse proxy only.

### Exposure control per service

- **Internet:** public DNS record exists + VPS SNI route configured (opt-in)
- **Tailscale:** Tailscale ACLs control mesh access
- **LAN:** reverse proxy listener binding + local firewall

## Success criteria

- Services reachable by `<name>.home.example.com` from all three network contexts (LAN, Tailscale, internet)
- Valid TLS in all contexts via a single wildcard cert issued with DNS-01
- Local DNS resolver returns LAN IPs for private-zone queries; forwards everything else upstream to NextDNS/Control-D
- Tailscale split DNS routes `home.example.com` queries to local resolver — no per-service Tailscale IP rewrites
- VPS performs SNI pass-through to homelab reverse proxy via WireGuard — no TLS termination on VPS
- Internet exposure is opt-in per service (public DNS record + VPS SNI route)

## Scope boundaries

**In scope:**

- Local DNS resolver (AdGuard Home or Technitium) authoritative for `home.example.com`
- Upstream forwarding to NextDNS or Control-D
- Tailscale split DNS configuration pointing `home.example.com` to local resolver
- Wildcard TLS cert issuance and renewal via Cloudflare DNS-01
- Reverse proxy (Caddy or Traefik) serving TLS-terminated services on homelab
- VPS SNI TCP pass-through configuration
- Per-service exposure control (LAN-only, Tailscale, internet)

**Out of scope:**

- Cloudflare Tunnel or any Cloudflare proxy-mode integration
- DNSSEC
- Dynamic DNS updates (zone is statically configured)
- mDNS or Avahi integration
- WireGuard mesh DNS (`.wg` zone for peer names) — separate concern from service exposure

## Open decisions

- **Reverse proxy:** Caddy vs Traefik
- **Local DNS resolver:** AdGuard Home vs Technitium

## Child artifacts

_Updated as Agent Specs and Spikes are created._

## Key dependencies

- EPIC-001 for WireGuard tunnel between VPS and homelab
- EPIC-005 for VPS provisioning (SNI pass-through configuration)
