---
title: "Linux/macOS Node Enrollment"
artifact: RUNBOOK-001
status: Active
mode: manual
trigger: on-demand
author: cristos
created: 2026-03-04
last-updated: 2026-03-04
validates:
  - SPEC-009
  - SPEC-003
  - SPEC-005
parent-epic: EPIC-007
depends-on: []
addresses:
  - JOURNEY-002.PP-03
  - JOURNEY-002.PP-04
---

# RUNBOOK-001: Linux/macOS Node Enrollment

## Purpose

Step-by-step procedure for enrolling a Linux Mint or macOS machine into the
Porthole fleet. Covers the full sequence from running `setup.sh` through to
verifying WireGuard connectivity and Guacamole access.

Use this runbook when:
- Enrolling a new machine for the first time.
- Re-enrolling a machine after re-imaging or hardware replacement.
- Verifying that an enrolled machine's services are correctly installed.

**Prerequisites for the automated path (TUI):** Once SPEC-009 Flow 4 is
implemented, steps 4–8 below will be handled by the TUI automatically.
Until then, follow the manual CLI steps.

## Prerequisites

- Hub is running and reachable (JOURNEY-001 complete).
- The repo is cloned on the target machine (or accessible via network share).
- The operator has `sudo` access on the target machine.
- The operator's age private key is at `~/.config/sops/age/keys.txt` on the
  target machine. If absent, see Step 2a.

## Steps

### 1. Run setup.sh to complete prerequisites and secrets

**Action:** From the repo root on the target machine, run:
```bash
./setup.sh
```

**Expected:** The Textual TUI opens at the Prerequisites screen.

---

**Action:** In the TUI, complete Steps 1–3 (Prerequisites, Secrets, Hub Check):
- Install any missing tools.
- If the age key is absent, use the TUI's "Transfer key from another machine"
  option to get the `scp` command, then run it from another enrolled machine.
  Alternatively, run manually:
  ```bash
  # On an already-enrolled machine:
  scp ~/.config/sops/age/keys.txt <target-machine>:~/.config/sops/age/keys.txt
  ```
- Confirm the hub is reachable in Hub Check.

**Expected:** All prerequisites green, secrets loaded, hub shows Reachable.

---

### 2a. (If TUI Flow 4 is available) Complete enrollment in TUI

**Action:** Proceed to Flow 4 in the TUI. Enter the node name, role, and
platform when prompted. The TUI will run `porthole add`, `porthole sync`,
`porthole gen-peer-scripts`, and `porthole install-peer` automatically.

**Expected:** TUI shows "Enrollment complete. WireGuard interface up."
Skip to Step 7.

---

### 2b. (Manual path) Register the peer in network state

**Action:** On the operator's primary machine (where you manage the fleet):
```bash
porthole add <node-name> --role workstation   # or --role server
# For a machine with a known platform:
porthole add <node-name> --role workstation --platform linux   # or macos
```

**Expected:** Output shows the new peer's WireGuard IP (e.g., `10.100.0.4`)
and a confirmation that it was added to `network.sops.yaml`.

---

### 3. Push updated configs to hub

**Action:** From the operator's primary machine:
```bash
porthole sync
```

**Expected:** Output shows configs uploaded to hub, services reloaded.
No errors.

---

### 4. Generate peer service files

**Action:** From the repo root on the target machine (or operator machine,
then transfer):
```bash
porthole gen-peer-scripts <node-name> --out ./peer-scripts/<node-name>
```

**Expected:** Directory `peer-scripts/<node-name>/` is created with:
- `wg0.conf` — WireGuard peer config
- `wg-watchdog.sh`, `wg-watchdog.service`, `wg-watchdog.timer` (Linux) or
  `wg-watchdog.plist` (macOS)
- `ssh-tunnel.service` (Linux) or `ssh-tunnel.plist` (macOS)
- `wg-status-server.py`, `wg-status-server.service` (Linux) or `.plist` (macOS)

---

### 5. Install WireGuard config and bring interface up

**Action (Linux):**
```bash
sudo cp peer-scripts/<node-name>/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable --now wg-quick@wg0
```

**Action (macOS):**
```bash
sudo cp peer-scripts/<node-name>/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
# macOS: use wg-quick or the WireGuard app to bring the tunnel up
wg-quick up wg0
```

**Expected:** `sudo wg show` shows the `wg0` interface with a peer entry for
the hub.

---

### 6. Install watchdog and reverse-tunnel services

**Action (Linux):**
```bash
# Watchdog
sudo cp peer-scripts/<node-name>/wg-watchdog.sh /usr/local/bin/wg-watchdog.sh
sudo chmod +x /usr/local/bin/wg-watchdog.sh
sudo cp peer-scripts/<node-name>/wg-watchdog.service /etc/systemd/system/
sudo cp peer-scripts/<node-name>/wg-watchdog.timer /etc/systemd/system/

# Reverse SSH tunnel
sudo cp peer-scripts/<node-name>/ssh-tunnel.service /etc/systemd/system/

# Status web server
sudo cp peer-scripts/<node-name>/wg-status-server.py /usr/local/bin/wg-status-server.py
sudo chmod +x /usr/local/bin/wg-status-server.py
sudo cp peer-scripts/<node-name>/wg-status-server.service /etc/systemd/system/

# Enable all services
sudo systemctl daemon-reload
sudo systemctl enable --now wg-watchdog.timer
sudo systemctl enable --now ssh-tunnel.service
sudo systemctl enable --now wg-status-server.service
```

**Action (macOS):**
```bash
sudo cp peer-scripts/<node-name>/wg-watchdog.plist /Library/LaunchDaemons/
sudo cp peer-scripts/<node-name>/ssh-tunnel.plist /Library/LaunchDaemons/
sudo cp peer-scripts/<node-name>/wg-status-server.plist /Library/LaunchDaemons/
sudo launchctl load -w /Library/LaunchDaemons/wg-watchdog.plist
sudo launchctl load -w /Library/LaunchDaemons/ssh-tunnel.plist
sudo launchctl load -w /Library/LaunchDaemons/wg-status-server.plist
```

**Expected (Linux):** `systemctl status wg-watchdog.timer ssh-tunnel.service
wg-status-server.service` all show `active`.

**Expected (macOS):** `launchctl list | grep porthole` shows all three daemons
in the list.

---

### 7. Verify WireGuard connectivity

**Action:** From the operator's primary machine:
```bash
porthole status
```

**Expected:** The new peer appears in the table with a handshake timestamp
within the last 2 minutes and non-zero Rx bytes.

**Action:** From the target machine:
```bash
ping hub.wg
ssh hub.wg
```

**Expected:** Ping succeeds. SSH connects to the hub.

---

### 8. Seed Guacamole connections (workstations only)

**Action:** From the operator's primary machine:
```bash
porthole seed-guac --apply
```
*(If `--apply` flag is not yet implemented, run `porthole seed-guac > /tmp/seed.sql`,
then apply manually:
`ssh hub.wg 'docker exec -i guacamole-postgres psql -U guacamole -d guacamole' < /tmp/seed.sql`)*

**Expected:** New connection entries for this peer appear in Guacamole.
Open Guacamole in a browser and verify the connection is listed.

---

### 9. (Linux workstation) Enable xrdp for Guacamole RDP access

**Action:**
```bash
sudo apt install -y xrdp
sudo systemctl enable --now xrdp
```

**Expected:** `systemctl status xrdp` shows active. From Guacamole, the RDP
connection to this peer opens a desktop session.

## Teardown

None — this procedure is an enrollment, not a test. To remove the node from
the fleet, run `porthole remove <node-name>` on the operator's machine and
`porthole sync`.

## Run Log

| Date | Executor | Result | Duration | Notes |
|------|----------|--------|----------|-------|
| 2026-03-04 | cristos | - | - | Runbook created |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-04 | 031aaaa | Initial creation — covers manual enrollment until SPEC-009 Flow 4 is implemented |
