# SPIKE-003: Hands-On Validation of Remote Access Contenders

**Status:** Planned
**Author:** cristos
**Created:** 2026-02-28
**Last Updated:** 2026-02-28
**Parent Vision:** [VISION-001](../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)
**Blocks:** Final product selection; determines whether EPIC-001 build path is needed

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|

---

## Question

The [product landscape](../../vision/(VISION-001)-Remote-Access-for-a-Personal-Fleet/product-landscape.md) identified multiple combinations that satisfy all requirements on paper. **Which one actually works best in practice?**

Desk research ([SPIKE-001](../\(SPIKE-001\)-Remote-Desktop-and-Mesh-Networking-Solutions/\(SPIKE-001\)-Remote-Desktop-and-Mesh-Networking-Solutions.md), [SPIKE-002](../\(SPIKE-002\)-Commercial-Remote-Desktop-Solution-Evaluation/\(SPIKE-002\)-Commercial-Remote-Desktop-Solution-Evaluation.md)) and the product landscape have narrowed the field. The remaining questions can't be answered by analysis — they require installing software on real machines and using it.

## Gate

**Pre-adoption / pre-build.** This spike determines whether to adopt an off-the-shelf combination or proceed with the EPIC-001 build path.

### Go criteria

All of the following, for at least one combination:

1. **Desktop quality is acceptable** on both fast networks (LAN / same-city) and slow networks (remote, different ISP). Responsive enough for interactive support sessions and sustained personal use.
2. **Family onboarding works.** The operator can set up a family member's machine (both apps installed, connected, tested) in under 30 minutes without the family member needing to understand what's happening.
3. **SSH works via Tailscale.** `ssh hostname` resolves via MagicDNS and connects without manual key management (Tailscale SSH).
4. **ACL isolation works.** Fleet machines on the tailnet cannot reach existing infrastructure (VMs, Docker, NAS) on the same tailnet.
5. **Stability over 48 hours.** Connections survive sleep/wake cycles and network changes without manual intervention.

### No-go pivot

If no contender combination passes all five criteria:

1. Identify which criteria failed and why.
2. Evaluate MeshCentral as a single-product fallback (accepts the SSH and isolation trade-offs).
3. If MeshCentral is also unacceptable, proceed with the EPIC-001 build path using whichever desktop tool performed best.

## Risks addressed

- Adopting a combination that looks good on paper but fails in daily use.
- Committing to a build when an install-and-go option would have been sufficient.
- Overlooking deal-breaking UX issues that only surface during real usage.

## Dependencies

- Tailscale account with free tier (100 devices / 3 users).
- At least 3 test machines: one Linux, one macOS, one Windows.
- At least 2 network locations (to test NAT traversal and remote performance).

## Test plan

### Combinations to test

1. **NoMachine + Tailscale** — both free, scored 7Y on paper.
2. **RustDesk + Tailscale** — both free, scored 7Y on paper. Better desktop UX expected.
3. **Splashtop + Tailscale** — $99/yr + free Tailscale, scored 6Y 1P. Include if Linux desktop quality gap is tolerable.

### Test matrix

| Test | What to measure | Pass threshold |
|------|-----------------|----------------|
| Desktop quality (fast network) | Responsiveness, visual quality, input lag | Comfortable for 30+ minute interactive session |
| Desktop quality (slow network) | Same, over remote connection | Usable for support tasks (doesn't need to be great) |
| Cross-platform | Connect from each OS to each OS | All 9 combinations work (3 client × 3 host) |
| Family onboarding | Time and steps to set up a new machine | Under 30 minutes, operator-only |
| SSH via Tailscale | MagicDNS resolution, Tailscale SSH | `ssh hostname` works from terminal without key setup |
| ACL isolation | Fleet machines vs. existing infra | Fleet machines cannot ping/reach non-fleet tailnet resources |
| Sleep/wake stability | Reconnect after sleep, network change | Auto-reconnects within 60 seconds, no manual intervention |
| 48-hour soak | Leave installed, use normally for 2 days | No crashes, no manual restarts, no config drift |

### Deliverable

A short write-up (in this spike folder) documenting:
- Results per combination per test
- Which combination is selected and why
- Whether the EPIC-001 build path is needed or if the base combo is sufficient
- Any surprises or deal-breakers discovered
