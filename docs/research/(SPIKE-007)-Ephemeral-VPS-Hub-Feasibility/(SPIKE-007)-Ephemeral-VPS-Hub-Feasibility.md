# SPIKE-007: Ephemeral VPS Hub Feasibility

**Status:** Complete
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent:** ADR-004 (WireGuard Hub-and-Spoke Relay)
**Question:** Is it operationally feasible to run the WireGuard hub as an ephemeral, on-demand VPS — destroyed when not in use — rather than as a persistent server?
**Gate:** Pre-ADR
**Risks addressed:**
  - 24/7 hub running as an internet-exposed surface even when no remote access is needed
  - Cost of always-on VPS for infrequent remote access
  - Complexity of a create/destroy lifecycle versus a simpler stop/start model

---

## Question

The current design (ADR-004) assumes a persistent hub running WireGuard relay, CoreDNS (`.wg` zone), Guacamole, and SSH relay. The operator wants to minimize attack surface by not running the hub 24/7. Is it feasible to spin the hub up only when remote access is needed, then destroy it? What does that require from providers, tooling, DNS, and WireGuard itself?

## Go / No-Go Criteria

- **Go:** Cold start (API call to usable hub) under 10 minutes from a fresh build (no snapshots), IP stability solved via DNS without manual peer reconfiguration, Terraform+cloud-init automation achievable, all hub state derived from git repo.
- **No-go:** DNS propagation lag exceeds 5 minutes, or WireGuard peers require manual restart on every hub recreation, or hub secrets cannot be safely managed outside Terraform state.

## Pivot Recommendation

If the full ephemeral model is operationally too fragile (DNS propagation delays, cloud-init reliability), fall back to the **hybrid model**: an always-on minimal hub (~€3.85/month) running only WireGuard + firewall, with Guacamole/CoreDNS started on demand via Docker Compose. This preserves the DNS-based endpoint (and therefore provider portability) while eliminating the spin-up delay for WireGuard connectivity.

---

## Findings

### 1. VPS Provider APIs for On-Demand Spin-Up

All major providers expose a REST API and a Terraform provider that can create and destroy VMs programmatically. The key metric for this use case is **cold-start time** — the elapsed time from API call to an SSH-accessible VM (kernel up, network configured, sshd listening). Cloud-init/user-data bootstrapping runs *after* this point and adds additional time.

| Provider | Terraform Provider | CLI Tool | Cold-Start (API→SSH) | Billing Model | Stopped VM Cost |
|----------|--------------------|----------|-----------------------|---------------|-----------------|
| **Hetzner Cloud** | `hetznercloud/hcloud` (mature) | `hcloud` | ~25 s (median, VPSBenchmarks 2024) | Per-hour, capped at monthly | **Full rate** — stopped VMs still billed |
| **DigitalOcean** | `digitalocean/digitalocean` | `doctl` | ~45 s (VPSBenchmarks 2024) | Per-hour | **Full rate** — powered-off Droplets still billed |
| **Vultr** | `vultr/vultr` | `vultr-cli` | ~99 s avg, 30–260 s range (VPSBenchmarks 2024) | Per-hour | **Full rate** — stopped instances still billed |
| **Linode/Akamai** | `linode/linode` | `linode-cli` | ~70 s (VPSBenchmarks 2024) | Per-hour | **Full rate** — powered-off instances still billed |
| **AWS Lightsail** | `hashicorp/aws` (`aws_lightsail_instance`) | `aws` CLI | Variable; Terraform provisioning reports can exceed expected times; typical 1–3 min | Per-hour, monthly cap | **Full rate** — stopped instances still billed |

**Key finding:** Every provider charges the full hourly rate for a stopped VM because resources remain reserved on the hypervisor. The only way to stop billing is to delete the VM. This confirms that the **create/destroy model is the correct approach** if cost minimization is the goal — stop/start saves you nothing financially compared to running it all the time, unless combined with a reserved IP (additional small cost).

**Cheapest option for this workload:** Hetzner Cloud CAX11 (Arm64, 2 vCPU, 4 GB RAM) at ~€3.29/month, which works out to ~€0.0049/hour. Running the hub for 10 hours/month costs less than €0.05. The smallest x86 type (CX22) is ~€3.85/month / €0.006/hour.

**Full bootstrap time (VM creation + cloud-init + WireGuard up + Guacamole ready):** Empirical reports and the cloud-init/Guacamole documentation consistently put this at **3–8 minutes** for a fresh install pulling packages from the internet. Pre-baked images (snapshots) can cut this to **under 2 minutes** by eliminating the package download phase.

### 2. The IP Address Problem

WireGuard peer configurations hardcode the hub's endpoint as an IP address or hostname. When the hub is destroyed and recreated, it typically receives a new IP. There are three clean solutions:

#### Solution A: Floating / Reserved IP (Zero-Delay, Provider-Locked)

Every major provider offers a static IP that persists independently of any VM instance. The IP can be assigned to a new VM after creation.

| Provider | Name | Cost (unassigned) | Cost (assigned) | Survives VM delete? |
|----------|------|-------------------|-----------------|----------------------|
| Hetzner Cloud | Floating IP | €3.00/month (IPv4), €1.00/month (IPv6) | Same | Yes |
| DigitalOcean | Reserved IP | $5.00/month ($0.01/hr) unassigned | Free | Yes |
| Vultr | Reserved IP | Hourly rate applies when unassigned | Per-instance pricing | Yes |
| AWS Lightsail | Static IP | Free when attached | Free | Yes (Lightsail-specific) |

**Hetzner workflow with Terraform:**
```hcl
# The floating IP lives outside the server lifecycle
resource "hcloud_floating_ip" "hub" {
  type      = "ipv4"
  home_location = "nbg1"
}

resource "hcloud_server" "hub" {
  name        = "wg-hub"
  server_type = "cx22"
  image       = "ubuntu-24.04"
  location    = "nbg1"
  user_data   = file("cloud-init.yaml")
}

resource "hcloud_floating_ip_assignment" "hub" {
  floating_ip_id = hcloud_floating_ip.hub.id
  server_id      = hcloud_server.hub.id
}
```

Running `terraform destroy -target=hcloud_server.hub` destroys the VM while leaving `hcloud_floating_ip.hub` intact. The next `terraform apply` creates a new VM and reassigns the same IP. **Peers never see an IP change.**

**DigitalOcean equivalent:** `digitalocean_reserved_ip` + `digitalocean_reserved_ip_assignment`. Reserved IPs persist across Droplet deletion and are free when assigned.

**AWS Lightsail:** Static IPs are free when attached, but Lightsail static IPs are region-scoped and cannot be re-attached via the standard AWS Elastic IP mechanism — use the Lightsail API (`attach-static-ip` action).

#### Solution B: DNS-Based Endpoint (Recommended — Provider-Portable)

WireGuard peers can use a hostname as the `Endpoint` value instead of a literal IP. However, **WireGuard resolves hostnames only at startup** — it does not re-resolve when the tunnel goes stale or when the peer becomes unreachable. If the hub's IP changes, existing peers will continue sending to the old IP until the WireGuard interface is restarted.

The official workaround is the `reresolve-dns.sh` script included in the `wireguard-tools` package:

```bash
# Recommended cron / systemd timer — runs every 30 seconds
*/1 * * * * /usr/share/doc/wireguard-tools/examples/reresolve-dns/reresolve-dns.sh wg0
```

This script calls `wg set wg0 peer <pubkey> endpoint <new-IP>:<port>` whenever the resolved address differs from the currently configured endpoint. It does this by re-parsing the wg-quick config files and re-resolving the hostname.

**TTL consideration with Cloudflare DNS:** Cloudflare free-tier DNS allows TTLs as low as 60 seconds on non-proxied records. Changes propagate globally within 5 minutes in practice (often under 1 minute from Cloudflare's authoritative servers). Combined with the 30-second reresolve-dns polling cycle, a hub recreation with a new IP would become reachable by peers within **90–120 seconds** of the DNS record update.

**This approach requires a DNS update step** in the Terraform workflow — either via a `cloudflare_record` Terraform resource or a post-creation script calling the Cloudflare API. Systemd or DuckDNS can serve the same role for smaller setups.

#### Solution C: Dynamic DNS (DuckDNS, Cloudflare DDNS) — Simpler but Less Reliable

A cloud-init script on the new hub can POST the new IP to DuckDNS or Cloudflare on first boot. Peers running `reresolve-dns.sh` on a 30-second timer will pick it up within 1–2 minutes of the DNS record propagating. This is operationally simpler than the floating-IP model but has more moving parts and a longer reconnection delay.

#### Provider portability via DNS

DNS-based endpoints decouple the hub's identity from any specific cloud provider. The peer WireGuard configs contain `Endpoint = hub.yourdomain.com:51820` — no IP, no provider-specific resource. This enables:

- **Provider hopping:** Create the hub on whichever provider has the best price, uptime, or geographic proximity today. Next month, switch to another. Terraform modules for each provider, one shared `cloudflare_record` resource.
- **Disaster recovery:** If a provider has an outage, spin up the hub on a different provider. Peers converge to the new IP within ~2 minutes.
- **No idle-cost infrastructure:** Floating IPs incur monthly charges even when no VM exists. A DNS record costs nothing beyond the domain registration.

The Cloudflare DNS account is already needed for Caddy's DNS-01 TLS challenge (SPIKE-005), so this adds no new accounts or infrastructure — just a Terraform `cloudflare_record` resource in the hub module.

**Recommendation:** Use DNS-based endpoints (Solution B). A few minutes' reconnection delay after hub creation is acceptable for this use case, and DNS-based endpoints unlock **provider portability** — the hub can be created on any provider (Hetzner, DigitalOcean, Vultr, etc.) without being locked to a provider-specific floating IP. The Cloudflare DNS record is already needed for SPIKE-005's DNS-01 TLS for Guacamole, so no new infrastructure is introduced. Floating IPs (Solution A) remain a valid optimization if zero-delay reconnection becomes a requirement later.

### 3. WireGuard Reconnection Behavior

Understanding WireGuard's timer constants is critical for this use case. The values are defined in `wireguard-go` and the kernel implementation:

| Constant | Value | Meaning |
|----------|-------|---------|
| `REKEY_TIMEOUT` | 5 s | How often a pending handshake initiation is retried |
| `REKEY_ATTEMPT_TIME` | 90 s | How long WireGuard tries to complete a handshake before giving up (ceasing retries and dropping queued packets) |
| `REJECT_AFTER_TIME` | 180 s | Sessions older than this are rejected; forces a new handshake |
| `KEEPALIVE_TIMEOUT` | 10 s | Idle time before a keepalive packet is sent (if `PersistentKeepalive` is set) |

**What happens when the hub goes away:**

1. Peers with `PersistentKeepalive` set will notice the hub is gone within seconds when keepalives stop being acknowledged.
2. A peer trying to send data will initiate a new handshake. WireGuard retries the handshake every 5 seconds.
3. After 90 seconds of failed handshake attempts, WireGuard's `REKEY_ATTEMPT_TIME` expires: it stops retrying and drops queued packets. **The peer enters a silent-fail state.**
4. When new data is queued (user triggers a new connection attempt), WireGuard restarts the handshake initiation cycle automatically.

**What happens when the hub comes back (same IP — floating IP or same provider):**

- The hub comes up with the same IP and the same WireGuard config from git.
- Peers that are still in the 90-second retry window will complete the handshake automatically.
- Peers that have already given up (past the `REKEY_ATTEMPT_TIME`) will restart the handshake cycle the next time they have traffic to send — no manual intervention required.
- **WireGuard does not require a service restart on the peer side.** The protocol is designed to self-heal.

**What happens when the hub comes back with a new IP (DNS-based endpoint — the recommended model):**

- Peers are configured with `Endpoint = hub.yourdomain.com:51820`.
- The Terraform workflow updates the Cloudflare DNS A record as part of `terraform apply`.
- Peers running `reresolve-dns.sh` on a 30-second timer re-resolve the hostname and call `wg set wg0 peer <pubkey> endpoint <new-IP>:<port>`. No service restart needed.
- Combined delay: DNS propagation (~60–120 s) + reresolve polling (~30 s) = **~90–150 seconds** from DNS update to reconnection.
- The SPIKE-006 Layer 1 watchdog can incorporate the reresolve logic directly, eliminating the need for a separate cron job.

**PersistentKeepalive consideration:** Setting `PersistentKeepalive = 25` on spoke peers helps maintain NAT mappings while the hub is up. When the hub is down, it causes rapid detection of the outage (within 25 seconds) rather than waiting for a timeout. There is no meaningful downside to having this set — the periodic UDP packet is negligible traffic. However, it does mean spokes will immediately notice and begin retrying handshakes the moment the hub goes offline, which is the desired behavior.

**Do nodes need to restart WireGuard when the hub is instantiated?** No. The full reconnection sequence is automatic:

1. Hub is created → Terraform updates Cloudflare DNS A record with the new IP.
2. Nodes have `Endpoint = hub.yourdomain.com:51820` and `PersistentKeepalive = 25` in their WireGuard config.
3. The node agent's watchdog (SPIKE-006 Layer 1) runs `reresolve-dns.sh` logic on a 30-second timer, which re-resolves `hub.yourdomain.com` and calls `wg set wg0 peer <hub-pubkey> endpoint <new-IP>:51820` if the IP changed.
4. The next PersistentKeepalive packet (within 25 seconds) triggers a handshake attempt to the new IP. The hub responds, handshake completes.
5. The tunnel is up. No restart, no manual intervention, no family member involvement.

The entire reconnection happens within **~2–3 minutes** of the DNS record updating — overlapping with cloud-init, so by the time the hub's WireGuard is actually listening, most nodes have already resolved the new IP and are retrying.

**Does WireGuard resume established connections?** No. TCP sessions that were routed through the tunnel drop (the tunnel going down is equivalent to a network partition for the TCP stack). After the hub returns and the WireGuard handshake completes, new TCP connections can be made. The user will need to reconnect their SSH session or refresh their Guacamole browser connection — the sessions themselves do not survive the hub cycle.

### 4. Terraform for VPS Lifecycle

Terraform with the Hetzner provider can manage the full create/destroy cycle. The operational sequence is:

```
terraform apply     # Creates server → gets new IP
                    # Updates Cloudflare DNS A record (hub.yourdomain.com → new IP)
                    # cloud-init bootstraps everything from scratch
                    # Hub is reachable in ~5–8 min

# ... operator uses remote access ...

terraform destroy   # Destroys server completely
                    # Hub is gone; nodes lose mesh connectivity
                    # Cost: €0 — nothing persists
```

**Total elapsed time (fresh build every time — no snapshots):**
- VM creation → SSH: ~25 s (Hetzner)
- cloud-init: install WireGuard, Docker; pull Guacamole/CoreDNS images; configure and start services: 3–7 min (variable, depends on upstream package mirrors and Docker Hub)
- DNS propagation to Cloudflare: ~60–120 s (overlaps with cloud-init)
- **Total: ~5–8 minutes**

**Why no snapshots:** The hub is fully defined by repo state. Every hub instance is built from scratch by cloud-init, ensuring:
- No configuration drift between git and the running system
- No snapshot maintenance or storage cost
- True provider portability — cloud-init works on any provider, snapshots are provider-specific
- Every boot is a clean, auditable build from known inputs

**Key management for fresh builds:** The hub's WireGuard private key and all peer configurations are SOPS/age-encrypted in the git repo. The fresh-build workflow:

1. cloud-init receives a `user_data` payload from Terraform containing the age identity key (or a reference to it).
2. cloud-init clones the git repo (or Terraform templates the config files into `user_data` directly).
3. SOPS decrypts `network.sops.yaml` using the age key → WireGuard configs are generated and written.
4. WireGuard, Docker Compose (Guacamole + CoreDNS), and supporting services start.

The age identity key is the one secret that must be injected from outside the repo. Options:
- **Terraform variable** passed via `TF_VAR_age_key` environment variable (never in state if marked `sensitive` + TF 1.10+ `ephemeral`)
- **Provider secret store** (Hetzner doesn't have one; use a `local_sensitive_file` or environment variable)
- **Operator's machine** — the `hub-up.sh` wrapper reads the key from the operator's local keyring/GPG agent and passes it to Terraform

**Terraform state management:** Terraform state must not be committed to git in plaintext because it can contain provider API tokens, private key material injected via variables, and resource metadata. Options:

| Backend | Cost | Appropriate for this project? |
|---------|------|-------------------------------|
| Hetzner Object Storage (S3-compatible) | ~€0.01/month for tiny state | Yes — stays within Hetzner, supports state locking |
| Terraform Cloud (free tier) | Free up to 500 resources | Yes — simple, managed locking |
| Local file + SOPS-encrypted | Free | Yes, but no remote locking; fine for solo use |
| Committed to git in plaintext | Free | **No** — state file contains sensitive values even when variables are marked `sensitive` |

**SOPS and Terraform:** The `carlpett/sops` Terraform provider can decrypt SOPS-encrypted `.yaml`/`.json` files at plan time, making secrets available to resources without them appearing in Terraform config. As of Terraform 1.10+, `ephemeral` resources prevent secret values from being persisted in state. For this project's scale, SOPS-encrypted variables + local state (gitignored) or Terraform Cloud state is the practical path.

**What Terraform cannot fully automate:** Terraform's `terraform apply` runs cloud-init and then marks the resource as "created" — it does not wait for cloud-init to complete. A `null_resource` with a `remote-exec` provisioner that checks for a sentinel file written at the end of cloud-init can gate further Terraform operations on bootstrap completion. Alternatively, a simple wrapper script (`spin-up-hub.sh`) can call `terraform apply` and then poll SSH until the WireGuard interface is confirmed up.

### 5. Stop/Start vs. Create/Destroy

The operator asked about both models. Here is a direct comparison:

| Dimension | Create/Destroy | Stop/Start |
|-----------|---------------|------------|
| **Cost when inactive** | €0 for VM (+ €3/month floating IP) | Full hourly rate (~€3.29/month for smallest Hetzner) |
| **IP stability** | Floating IP required; otherwise new IP each time | IP changes on restart unless reserved IP used |
| **Spin-up time** | 25 s (VM) + 3–8 min cloud-init (or 90 s from snapshot) | 20–30 s boot time; services start from existing state |
| **Attack surface when inactive** | None — VM does not exist | VM exists on the hypervisor; local kernel is running |
| **Config freshness** | Always from git state on creation | State from last shutdown; may diverge from git |
| **Operational complexity** | Slightly higher (Terraform lifecycle, snapshot maintenance) | Simpler (just start/stop API call) |
| **State management** | Fresh from git every time (desired behavior) | May have drift between git and running state |

**Stop/Start practical note:** Hetzner charges full rate for stopped VMs. At ~€3.29/month for the smallest ARM instance, this is already cheap. But the attack surface argument holds: a stopped Hetzner server still has an IP assigned, kernel running (in a stopped hypervisor state), and could potentially be started by an attacker with account access. A destroyed server does not exist at all.

**Verdict:** If cost is the only driver, stop/start and create/destroy have similar costs once a reserved IP is included (~€3/month IP for create/destroy vs. ~€3.29/month VM for stop/start). Create/destroy wins on the attack surface argument and on config-freshness guarantees. **Create/destroy from snapshot with a floating IP is the recommended model.**

### 6. The "No Hub at All" Model: P2P WireGuard

The operator asked whether WireGuard could work peer-to-peer for SSH without a relay.

**WireGuard and NAT traversal:** WireGuard uses UDP. UDP hole-punching (the technique behind P2P traversal) works by having both peers simultaneously send packets to each other's external NAT address, relying on the NAT to keep the "hole" open. This is precisely what Tailscale's STUN + DERP model does on top of WireGuard.

**Vanilla WireGuard does not implement hole-punching.** It assumes that at least one peer has a routable public IP (the hub). Without a hub, vanilla WireGuard requires both nodes to have public IPs, which is not the case for residential NAT.

**What percentage of residential NATs support hole-punching?** From Tailscale's published research:
- Full-cone and restricted-cone NATs: easily traversed — the majority of home routers fall here.
- Symmetric NATs: cannot be hole-punched with standard techniques — common in corporate environments, some ISPs (CGNAT), and strict mobile carriers.
- Tailscale's combined STUN + DERP approach achieves direct connections "over 90% of the time" when combining all techniques, but relies on DERP relay servers for the remainder.

**Failure scenarios for a family fleet:**
- ISP-level CGNAT (carrier-grade NAT, widespread in mobile and some cable ISPs): both ends are behind the same large NAT — hole-punching fails.
- Double NAT (modem + router): common in homes using ISP-provided modems in bridge-fail mode — hole-punching reliability drops significantly.
- One side is a domestic Wi-Fi network that reassigns ports aggressively (symmetric NAT behavior).

**Conclusion:** Pure P2P WireGuard (without a STUN signaling mechanism and a fallback relay) fails in 10–30% of residential scenarios, concentrated exactly in the cases that matter most (mobile hotspots, travel, CGNAT ISPs). The hub model is not just a convenience — it is a reliability requirement for a family fleet.

If the hub is down and the operator is trying to reach a node from a network where direct P2P is not possible, **there is no path in**. This is the core operational tension of the ephemeral model.

**Tailscale as an alternative:** Tailscale implements WireGuard + STUN + DERP relay and handles all of this transparently. For a family fleet this is the path of least resistance. The decision to build a custom hub (ADR-004) accepts the operational complexity in exchange for no SaaS dependency and full data sovereignty.

### 7. Security Implications of Ephemeral vs. Persistent Hub

#### Attack Surface Analysis

A 24/7 hub exposes four services to the internet:
- WireGuard UDP port (51820 or similar) — extremely low attack surface; WireGuard ignores all traffic that doesn't present a valid handshake
- Guacamole HTTPS — web-accessible; needs TLS, auth hardening (see SPIKE-005)
- CoreDNS (bound to WireGuard interface only, not internet-facing)
- SSH relay (should be bound to WireGuard interface only, not internet-facing)

The genuine risk on a persistent hub is:
- Kernel vulnerabilities in the WireGuard module (rare but real)
- Guacamole web application vulnerabilities (more frequent; Apache Guacamole CVEs are published regularly)
- The host OS itself (unpatched packages, misconfigured firewall rules)

An ephemeral hub eliminates these attack windows entirely when not in use. The hub exists only during active remote access sessions.

#### The Operational Catch

The ephemeral model creates a significant operational constraint:

> **The operator cannot access any node without first spinning up the hub.**

For planned remote access ("I'm working from home today, I'll bring the hub up"), this is acceptable — a 90-second warm-up from snapshot is a modest price. For reactive access ("my mom's computer is broken, let me check it right now"), the 90-second delay is fine but requires the operator to:

1. Have Terraform (or a wrapper script) available on whatever device they're using
2. Have access to the git repo and decrypted SOPS secrets (or a CI/CD trigger)
3. Wait for the hub to come up before any node is reachable

If the operator is traveling without their main machine, none of this works. Options:

- **Trigger script accessible from a phone:** A simple HTTPS endpoint (Cloudflare Worker, GitHub Actions `workflow_dispatch`, or a Hetzner server action webhook) that calls `terraform apply` when hit with an auth token. The hub comes up without needing Terraform locally.
- **Always-on lightweight hub:** Accept a $3–5/month cost for a tiny persistent VM that runs only WireGuard + a firewall (no Guacamole, no DNS exposed). Guacamole and CoreDNS spin up on demand on top of the always-on relay. This hybrid model maintains mesh connectivity 24/7 while only exposing the minimal WireGuard surface permanently.
- **Tailscale as the 24/7 fallback (SPIKE-006 Layer 3):** The existing defense-in-depth stack from SPIKE-006 already includes a passive Tailscale install on each node. In an emergency where the hub is down and can't be spun up quickly, the operator enables Tailscale on the target node (remotely via a phone call to the family member) and uses `tailscale ssh` as an out-of-band channel.

#### Node-to-Node Connectivity When Hub Is Down

All inter-node routing in the hub-and-spoke model routes through the hub. When the hub is destroyed:
- Nodes cannot reach each other
- The `.wg` DNS zone is offline (CoreDNS is on the hub)
- Guacamole is offline

This is by design in the ephemeral model. The family fleet is isolated when the hub is down. For a homelab with ~10 nodes that mostly operate independently (no node-to-node services), this is acceptable. For a scenario where nodes continuously communicate with each other (e.g., a NAS that nodes sync to over the VPN), the ephemeral model breaks that use case.

---

## Recommended Architecture

Based on the above findings and the operator's acceptance of a few minutes' spin-up delay, the DNS-based ephemeral model is recommended. A few minutes to bring the hub online is acceptable; provider portability and zero idle cost are more valuable than instant reconnection.

### Recommended: Full Ephemeral with DNS Endpoint, Fresh Build Every Time

- **DNS endpoint:** All peer WireGuard configs use `Endpoint = hub.yourdomain.com:51820`. No floating IP, no provider lock-in.
- **Terraform module** per provider (Hetzner, DigitalOcean, etc.) in the git repo manages the server lifecycle. A shared `cloudflare_record` resource updates the DNS A record after VM creation.
- **Fresh build from repo state:** No snapshots. Every hub instance is built from scratch by cloud-init — install packages, decrypt SOPS/age keys from git, generate WireGuard configs, pull Docker images, start services. This ensures the running hub always matches the repo and eliminates provider-specific snapshot management.
- **Wrapper script** (`hub-up.sh` / `hub-down.sh`) wraps `terraform apply` and `terraform destroy`, waits for cloud-init completion + DNS propagation, prints status.
- **On each peer node:** `Endpoint = hub.yourdomain.com:51820`, `PersistentKeepalive = 25`. The node agent watchdog (SPIKE-006 Layer 1) incorporates `reresolve-dns.sh` logic to pick up the new IP within 30 seconds of DNS propagation. **No node restart needed** — reconnection is fully automatic (see section 3).
- **Mobile trigger:** GitHub Actions `workflow_dispatch` or similar webhook, triggerable from the GitHub mobile app.
- **Spin-up timeline:** VM creation (~25 s) + cloud-init fresh build (~3–7 min) + DNS propagation (~60–120 s, overlaps with cloud-init) = **~5–8 minutes** from trigger to operational hub.
- **Total inactive cost:** €0. Domain registration is a sunk cost (already needed for Caddy DNS-01 TLS).
- **Total active cost:** ~€0.006/hour (Hetzner CAX11).
- **Provider portability:** Switch providers by changing the Terraform module. Cloud-init is provider-agnostic. Peers don't care — they resolve the DNS name.

### Alternative: Hybrid (24/7 Relay + On-Demand Services)

If the full ephemeral model proves too operationally fragile (e.g., DNS propagation delays are worse than expected, or the operator needs instant node access for monitoring), fall back to:

- **Always-on minimal hub** (~€3.85/month) running only WireGuard and a strict firewall. Nodes stay connected 24/7. Attack surface: one UDP port.
- **Guacamole + CoreDNS:** Started/stopped via Docker Compose when remote desktop access is needed (~10–20 seconds).
- **DNS endpoint still works here** — the hub's IP doesn't change, but peers use the DNS name anyway for consistency. This preserves the option to go full ephemeral later.
- **Total cost:** ~€3.85/month flat.

The hybrid model is the fallback if ephemeral doesn't work in practice. Start with full ephemeral; degrade to hybrid if the spin-up delay or DNS lag causes real problems.

---

## Summary Verdict

| Question | Answer |
|----------|--------|
| Is create/destroy feasible? | Yes. Fresh build via cloud-init, ~5–8 min to fully operational. No snapshots — repo is authoritative. |
| Floating IP or DNS? | **DNS.** A few minutes' delay is acceptable. DNS enables provider portability and eliminates the €3/month floating IP. Cloudflare account already needed for TLS (SPIKE-005). |
| Does WireGuard reconnect after DNS change? | Yes, via `reresolve-dns.sh` (bundled with wireguard-tools). Peers pick up the new IP within ~30 s of DNS propagation. No restart needed. |
| Can Terraform manage the lifecycle? | Yes. `hcloud` provider is mature. State must not go in git. `cloudflare_record` updates DNS automatically. |
| Stop/start vs. create/destroy? | Create/destroy wins on attack surface and config freshness. No cost difference once floating IP is removed from the equation. |
| P2P without hub? | Not viable for residential fleet. ~10–30% failure rate across NAT types. |
| Provider portability? | Yes — DNS endpoint + per-provider Terraform module. Switch providers by changing one variable. |
| Do nodes need to restart WireGuard? | No. `PersistentKeepalive` + `reresolve-dns.sh` in the node agent handles reconnection automatically. |
| Can it build fresh every time (no snapshots)? | Yes. cloud-init + SOPS/age-encrypted keys from git. ~5–8 min. True IaC — repo is the single source of truth. |
| Is ephemeral operationally viable for emergency access? | Yes, with a mobile trigger (GitHub Actions `workflow_dispatch`, webhook). ~5–8 min from trigger to operational hub. |
| Best overall recommendation? | **Full ephemeral with DNS.** Fall back to hybrid (always-on WireGuard + on-demand Guacamole) if spin-up delay causes real problems. |

---

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Complete | 2026-02-28 | 3abdcad | Created directly in Complete phase; all findings resolved in single research session; informs ADR-004 |
