# MVP Open Questions

**Supporting doc for:** [VISION-001](./(VISION-001)-Remote-Access-for-a-Personal-Fleet.md)
**Created:** 2026-02-28

Instructions: answer each question inline below the prompt. Your answers will
drive artifact updates (epic scoping, ADR amendments, spike disposition).
Write as much or as little as you want — a sentence is fine, a paragraph is
fine, "yes" / "no" / "defer" is fine.

---

## 1. Repo boundary

The fleet agent (WireGuard + native remote-desktop protocols) targets servers,
family machines, and non-dev workstations — not just the operator's
workstation. This repo started as a workstation bootstrapper.

**Should the fleet agent live in this repo or a separate one?**

If separate: how does the workstation repo consume it? (Git submodule, Ansible
Galaxy role, standalone with loose coupling, or something else?)

> **Answer:** This is a stream-aligned repo and should contain **both** domains. It should be idempotent -- running it on a workstation will confirm it can reach the gateway; if it can't, it will ask for what is necessary to do so, or if it should spin up a new one.

---

## 2. Guacamole deployment location

Guacamole needs to be reachable from any node on the WireGuard network. Three
options:

- **Homelab only** — runs alongside other homelab services. Not reachable when
  traveling unless the homelab itself is a WireGuard node.
- **VPS** — always reachable from anywhere, but adds services to the VPS
  (Tomcat + guacd + database). Conflicts slightly with "VPS runs no services
  beyond WireGuard, CoreDNS, SSH, and the status script" (EPIC-005).
- **Both** — homelab as primary, VPS as fallback, or vice versa.

**Where should the Guacamole gateway run?**

> **Answer:** VPS, but still as dumbly as possible. Consolidate the hub, make it fully fungible. If we have to destroy the hub/it is lost, we shouldn't lose anything and be able to spin up a new one with minimal-to-no interaction.

---

## 3. Operator Dashboard (EPIC-004) — keep, cut, or re-scope?

Guacamole provides a web UI with connection management for all machines.
EPIC-004 was designed before Guacamole was adopted and overlaps significantly.

The gap Guacamole does NOT cover: WireGuard-level telemetry (last handshake
time, transfer bytes, tunnel up/down status, endpoint changes). Guacamole only
knows whether it can connect via RDP/VNC/SSH — it doesn't see the network
layer.

Options:
- **Keep as-is** — build a separate dashboard for WireGuard health.
- **Re-scope** — narrow EPIC-004 to WireGuard tunnel monitoring only
  (complement to Guacamole, not replacement).
- **Cut** — defer or abandon. The operator can SSH to the VPS and run
  `wg show` manually. A dashboard is nice-to-have, not MVP.

**What should happen to EPIC-004?**

> **Answer:** re-scope -- it would be helpful to know the wireguard disposition of machines.

---

## 4. Client Node Web UI (EPIC-003) — keep, cut, or re-scope?

EPIC-003 puts a small web UI on each client node showing tunnel status and a
"restart tunnel" button. The use case is walking a family member through a
restart over the phone.

With Guacamole, the operator can SSH to the family machine directly and
restart the tunnel. The per-node web UI saves one step (family member opens a
browser instead of the operator SSHing in).

**Is the per-node web UI worth building for MVP, or can it be deferred?**

> **Answer:** Um, no, we can't do that with Guacamole if the tunnel is down...

---

## 5. Family machine onboarding

ADR-004 acknowledges manual key distribution: the operator runs `wgmesh add`
to generate a config, then delivers it to the target machine. For family
machines operated by non-technical users, what does "deliver" mean?

Options:
- **Operator does it remotely** — SSHes into the family machine (requires SSH
  access before WireGuard is up, so the machine needs to be on Tailscale, or
  the operator does it in person first).
- **Operator does it in person** — walks over, plugs in a USB, or screen-shares
  to set it up. One-time visit per machine.
- **Family member does it with instructions** — operator sends a config file
  and a 3-step guide ("download this, install WireGuard, import this file").
- **Some combination** — in-person for initial setup, remote for updates.

**How do you expect to get WireGuard configs onto family machines?**

> **Answer:** Operator does it remotely, but might be via a side-channel (e.g., remotix, teamviewer, etc.)

---

## 6. SPIKE-003 — abandon or rewrite?

SPIKE-003 (Hands-On Validation) is still Planned. It was designed to test
NoMachine + Tailscale, RustDesk + Tailscale, and Splashtop + Tailscale. Since
then:

- ADR-004 replaced Tailscale with WireGuard
- ADR-005 replaced RustDesk with Guacamole + native protocols

The combinations SPIKE-003 planned to test no longer match the adopted
architecture.

Options:
- **Abandon** — the research spikes (001, 002, 004) and ADRs already cover
  the decision space. Hands-on validation happens during implementation.
- **Rewrite** — update SPIKE-003 to validate WireGuard + Guacamole + native
  RDP/VNC/SSH on real hardware before building the provisioning tooling.

**Should SPIKE-003 be abandoned or rewritten for the current stack?**

> **Answer:** abandon and write new spikes if needed

---

## 7. SPEC-002 — deprecate or rewrite?

SPEC-002 (Remote Desktop Bootstrap) is marked Implemented. It installs
RustDesk, GLI KVM, and Remmina. ADR-005 supersedes this — the new model is
native protocols + Guacamole gateway.

Options:
- **Deprecate** — mark SPEC-002 as Deprecated, write a new spec (SPEC-003?)
  for the Guacamole + native protocol setup.
- **Rewrite in place** — update SPEC-002's content to reflect the new model,
  keeping the artifact number.
- **Leave it** — SPEC-002 documents what was actually built. The new model
  gets its own spec when implementation begins. No action now.

**What should happen to SPEC-002?**

> **Answer:** deprecate.

---

## 8. MVP scope — which epics are in?

Given the decisions above, which epics constitute MVP? Check all that apply:

- [ ] **EPIC-001** — Remote Fleet Management (umbrella epic)
- [ ] **EPIC-002** — Provisioning CLI (`wgmesh` tool)
- [ ] **EPIC-003** — Client Node Web UI (per-node status page)
- [ ] **EPIC-004** — Operator Dashboard (network-wide status view)
- [ ] **EPIC-005** — VPS Bootstrap & Disaster Recovery
- [ ] **EPIC-006** — Internal DNS Resolution (CoreDNS `.wg` zone)
- [ ] **Guacamole deployment** (not yet an epic — should it be?)

**Which epics are MVP, and which are post-MVP?**

> **Answer:** let's revisit all epics, based on refined vision and answers above. start from scratch. where do requirements like these live? node provisioning (more than wgmesh, that might be part of it; would include polling git repo for topology and decrypting it, using magic wormhole to transfer initial keys, etc.); textual app for client UI (no web UI anymore, but something that can be run over SSH); SSH-ability from any one node to any other node (routed via hub is ok, but should be painless, not involve configuring forwarding every time); EPIC-005 (holds as-is); EPIC-006 (still relevant, but might not be the same shape with above changes?)

---

## 9. Anything else?

Anything not covered above that you want to clarify, add, or change before
speccing out the MVP epics?

> **Answer:**
