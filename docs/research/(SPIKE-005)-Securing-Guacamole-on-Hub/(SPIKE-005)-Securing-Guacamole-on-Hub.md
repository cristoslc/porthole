---
artifact: SPIKE-005
title: Securing Guacamole on the Hub
status: Complete
author: cristos
created: 2026-02-28
last-updated: 2026-02-28
parent-epic: EPIC-005
depends-on: []
---

# SPIKE-005: Securing Guacamole on the Hub

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent:** [EPIC-005](../../epic/Proposed/(EPIC-005)-VPS-Bootstrap/(EPIC-005)-VPS-Bootstrap.md)
**Question:** How should Guacamole be secured on a VPS that also serves as the WireGuard hub, given that the hub must be fully fungible and rebuildable?
**Gate:** Pre-MVP
**Risks addressed:**
  - Guacamole exposed to the public internet creates an attack surface
  - Connection state stored only on the VPS violates fungibility
  - TLS configuration must work without public DNS for the WireGuard-internal address

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-28 | a785ec8 | Research completed in conversation; informs EPIC-005 hub security design |

---

## Question

The VPS hub runs WireGuard (relay), CoreDNS, and Guacamole. Guacamole must be reachable from any WireGuard node but not from the public internet. The hub must be fully fungible — destroyable and rebuildable from repo state with no manual configuration. How do we secure Guacamole in this context?

## Go / No-Go Criteria

- **Go:** Guacamole is reachable only from inside the WireGuard tunnel, TLS is automated, connections are generated from repo state, and the entire hub is rebuildable with one command.
- **No-go:** If securing Guacamole requires manual steps that break fungibility or if the attack surface cannot be reduced to WireGuard + SSH only.

## Pivot Recommendation

If Guacamole cannot be adequately secured on the VPS, run it on the operator's homelab behind WireGuard instead (accepting reduced availability when traveling).

## Findings

### 1. Network exposure: bind to WireGuard only

Guacamole should never be reachable from the public internet. All services bind to the WireGuard interface IP only:

| Service | Bind address | Port | Exposure |
|---------|-------------|------|----------|
| Caddy (reverse proxy) | `10.100.0.1` | 443 | WireGuard peers only |
| Tomcat (Guacamole) | `127.0.0.1` | 8080 | Loopback only |
| guacd | `127.0.0.1` | 4822 | Loopback only |
| PostgreSQL | Docker internal | 5432 | Docker network only |
| CoreDNS | `10.100.0.1` + `127.0.0.1` | 53 | WireGuard peers + loopback |

The public interface exposes **only**:
- UDP/51820 — WireGuard
- TCP/22 — SSH (for emergency host management)

Everything else is dropped by the firewall.

### 2. TLS: Caddy with DNS-01 challenge (recommended)

**Option A (recommended): DNS-01 with a public subdomain.**

Register a subdomain (e.g., `guac.yourdomain.com`) pointing to the WireGuard IP (`10.100.0.1` — a private address). DNS-01 validation happens at the registrar level, not by reaching the server. The cert is Let's Encrypt-signed (browser-trusted) but the service is unreachable from the public internet.

```
guac.yourdomain.com {
    tls {
        dns cloudflare {$CF_API_TOKEN}
    }
    bind 10.100.0.1
    reverse_proxy http://127.0.0.1:8080 {
        flush_interval -1
    }
}
```

Requires a custom Caddy build with the DNS provider plugin (`xcaddy build --with github.com/caddy-dns/cloudflare`). Auto-renews.

**Option B: Caddy `tls internal`.**

Caddy generates its own CA. Install the root cert on each fleet node. No public domain needed. One-time cert distribution to ~10 machines is manageable.

**Option C: Self-signed.** Acceptable given WireGuard already encrypts transport, but browsers show warnings unless the cert is installed in each client's trust store.

### 3. Authentication: database + TOTP with WireGuard bypass

Three layers:
1. **WireGuard tunnel** — only peers with a valid keypair can reach Guacamole
2. **Username/password** — database auth with one admin user
3. **TOTP** — via `guacamole-auth-totp` extension

TOTP can be bypassed for connections from the WireGuard subnet using `totp-bypass-hosts`:

```properties
# guacamole.properties
totp-bypass-hosts: 10.100.0.0/24
```

This means: if you're on the WireGuard network, username/password is sufficient. If somehow reached from an unexpected IP, TOTP is required.

Guacamole's built-in `guacamole-auth-ban` extension blocks repeated failed login attempts automatically.

### 4. Connection configuration: SQL seed from repo state

Guacamole stores connections in PostgreSQL. For fungibility, the database is seeded from a SQL file in the repo:

1. Schema: `docker run --rm guacamole/guacamole:1.6.0 /opt/guacamole/bin/initdb.sh --postgresql > init/01-schema.sql`
2. Seed: `init/02-seed.sql` with INSERT statements for connections, generated from `network.sops.yaml`
3. On `docker compose up`, PostgreSQL runs both SQL files from `/docker-entrypoint-initdb.d/`

The `wgmesh hub deploy` command should regenerate `02-seed.sql` from the current network state before deploying.

Alternative: Guacamole 1.6.0 supports batch import via JSON/YAML through the REST API, which could be used as a post-deploy step.

### 5. Deployment: Docker Compose (recommended)

Four containers:

| Container | Image | Role |
|-----------|-------|------|
| `guacd` | `guacamole/guacd:1.6.0` | Protocol proxy daemon |
| `guacamole` | `guacamole/guacamole:1.6.0` | Web app (Tomcat) |
| `postgres` | `postgres:15-alpine` | Auth + connection storage |
| `caddy` | Custom build with DNS plugin | TLS termination + reverse proxy |

WireGuard runs on the host (kernel module), not in Docker. CoreDNS can run either way.

State lives entirely in:
- `docker-compose.yml` — topology
- `init/*.sql` — database schema + seed
- `Caddyfile` — proxy/TLS config
- `guacamole.properties` — app config (TOTP, auth settings)

Rebuild: `git clone <repo> && docker compose up -d`

Docker credentials use `POSTGRES_PASSWORD_FILE` with Docker Secrets (not plaintext in compose files).

### 6. Firewall: nftables

Minimal nftables ruleset:

```nftables
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iifname lo accept
        ct state established,related accept
        ip protocol icmp accept
        iifname eth0 tcp dport 22 ct state new limit rate 5/minute accept
        iifname eth0 udp dport 51820 accept
    }
    chain forward {
        type filter hook forward priority 0; policy drop;
        iifname wg0 oifname wg0 accept
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

The `forward` chain allows spoke-to-spoke routing through the hub. All Guacamole/CoreDNS/Postgres ports are implicit-denied on the public interface because they bind to WireGuard or loopback addresses only.

### 7. Guacamole + WireGuard interaction

No fundamental conflicts. Key details:
- guacd initiates outbound connections to spokes via `wg0` — routing works automatically since the hub has `10.100.0.0/24 dev wg0`
- Docker bridge networks must not overlap with the WireGuard subnet (configure in `/etc/docker/daemon.json`)
- guacd should explicitly bind to `127.0.0.1` in `guacd.conf` to avoid an IPv6 binding mismatch
- WireGuard should run on the host, not in Docker, to avoid interface naming conflicts

### 8. Security baseline

- Run Guacamole 1.6.0+ (patches CVE-2024-35164: critical RCE via terminal injection)
- Docker images rebuild nightly against Alpine — `docker compose pull && docker compose up -d` picks up patches
- guacd runs as a non-root user inside its container
- PostgreSQL data volume is ephemeral — recreated from seed SQL on rebuild

### 9. Ephemeral hub model (see SPIKE-007)

SPIKE-007 evaluates whether the hub can be destroyed when not in use and recreated on demand. The recommended hybrid model — always-on WireGuard relay + on-demand Guacamole via Docker Compose — significantly changes the security profile:

- **Guacamole is not running 24/7.** The operator starts it with `docker compose up -d guacamole coredns` when remote desktop access is needed, and stops it afterward. The Guacamole attack surface (web application, Tomcat, PostgreSQL) exists only during active sessions.
- **All other findings in this spike remain valid** — network binding, TLS, authentication, SQL seeding, firewall rules apply whenever Guacamole is running.
- **The persistent attack surface reduces to WireGuard UDP only** — one of the narrowest possible surfaces for an internet-facing service.
