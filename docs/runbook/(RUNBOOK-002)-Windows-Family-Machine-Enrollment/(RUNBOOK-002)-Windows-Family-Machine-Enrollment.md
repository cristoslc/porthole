---
title: "Windows Family Machine Enrollment"
artifact: RUNBOOK-002
status: Active
mode: manual
trigger: on-demand
author: cristos
created: 2026-03-04
last-updated: 2026-03-04
validates:
  - SPEC-003
  - SPEC-004
  - SPEC-005
parent-epic: EPIC-001
depends-on: []
addresses:
  - JOURNEY-003.PP-01
  - JOURNEY-003.PP-02
  - JOURNEY-003.PP-03
  - JOURNEY-003.PP-04
---

# RUNBOOK-002: Windows Family Machine Enrollment

## Purpose

Step-by-step procedure for enrolling a Windows machine owned by a family
member (or any Windows node) into the Porthole fleet. The family member
does not need to be present for or understand any of these steps. All
configuration is performed by the operator, either in person or via an
existing remote session.

After completing this runbook:
- The Windows machine is on the `10.100.0.0/24` WireGuard mesh.
- The operator can reach it via Guacamole RDP from any enrolled node.
- The WireGuard tunnel reconnects automatically when Windows starts.

## Prerequisites

- Hub is running and reachable.
- The operator has an enrolled Linux or macOS machine (the "operator machine")
  with the Porthole repo checked out and `network.sops.yaml` decryptable.
- The operator has physical access to the Windows machine, or already has
  remote access (e.g., via TeamViewer or Windows Quick Assist) to set it up.
- The Windows machine has internet access.
- The operator has an admin account on the Windows machine.

## Steps

### Part A: On the Operator's Machine

### 1. Register the peer in network state

**Action:** From the repo root on the operator's machine:
```bash
porthole add <node-name> --role family --platform windows
```
Replace `<node-name>` with a short identifier (e.g., `dad-pc`, `mom-laptop`).

**Expected:** Output shows the peer's WireGuard IP (e.g., `10.100.0.5`) and
confirms it was added to `network.sops.yaml`.

---

### 2. Push updated hub config

**Action:**
```bash
porthole sync
```

**Expected:** Hub WireGuard config updated; the new peer's allowed IP is now
accepted by the hub. CoreDNS zone updated with `<node-name>.wg`.

---

### 3. Extract the peer WireGuard config

**Action:**
```bash
porthole peer-config <node-name> --out /tmp/<node-name>-wg0.conf
```

*(If `porthole peer-config` is not yet implemented, generate via gen-peer-scripts
and locate the conf file:)*
```bash
porthole gen-peer-scripts <node-name> --out ./peer-scripts/<node-name>
# The config is at: peer-scripts/<node-name>/wg0.conf
cp peer-scripts/<node-name>/wg0.conf /tmp/<node-name>-wg0.conf
```

**Expected:** The file `/tmp/<node-name>-wg0.conf` exists and contains:
- `[Interface]` with the peer's WireGuard IP and private key
- `[Peer]` with the hub's public key and endpoint

> **Security note:** This file contains the peer's WireGuard **private key**
> in plaintext. Transfer it using one of the methods in Step 4, then delete
> the local copy:
> ```bash
> # After transfer is confirmed:
> rm /tmp/<node-name>-wg0.conf
> ```

---

### 4. Transfer the config to the Windows machine

Choose the most secure option available:

**Option A — USB drive (most secure):**
Copy the `.conf` file to a USB drive. Carry it to the Windows machine.

**Option B — Temporary file share (local network only):**
If you are on the same local network:
```bash
# On the operator machine, start a quick HTTP server in /tmp:
cd /tmp && python3 -m http.server 8888 --bind 192.168.x.x
# On Windows: open browser → http://192.168.x.x:8888/<node-name>-wg0.conf
# Stop the server immediately after download.
```

**Option C — Existing remote session:**
If you already have a remote desktop or TeamViewer session to the Windows
machine, use the session's file transfer feature.

**Option D — Secure messaging:**
Send via iMessage, Signal, or a password manager's secure share. Do **not**
use unencrypted email or SMS.

**Expected:** The `.conf` file is on the Windows machine. Delete the copy
from the operator machine.

---

### Part B: On the Windows Machine

Perform the following steps as admin on the Windows machine.

### 5. Install WireGuard

**Action:** Download and run the WireGuard installer:
1. Open a browser and go to: `https://www.wireguard.com/install/`
2. Click **Download Windows installer** and run it.
3. Accept the UAC prompt.

**Expected:** WireGuard is installed and the system tray icon appears.

---

### 6. Import the WireGuard config

**Action:**
1. Open the WireGuard application.
2. Click **Import tunnel(s) from file**.
3. Navigate to and select the `<node-name>-wg0.conf` file you transferred.
4. The tunnel appears with the name matching the `[Interface]` `Address`.

**Expected:** The tunnel is listed in WireGuard with status "Inactive".

---

### 7. Activate the tunnel and configure auto-start

**Action:**
1. Select the tunnel and click **Activate**.
2. Check **Launch WireGuard minimized on startup** (System tray → right-click
   WireGuard icon → Settings).
3. In the tunnel's settings, ensure **Active on startup** is enabled.

**Expected:** Tunnel status changes to "Active". The Windows machine now has
IP `10.100.0.N` on the WireGuard interface.

---

### 8. Enable Remote Desktop

**Action:**
1. Open **Settings** → **System** → **Remote Desktop**.
2. Toggle **Enable Remote Desktop** to On.
3. Click **Confirm** on the prompt.
4. Note the user account name listed under "User accounts" (this is the
   username Guacamole will use to connect).
5. Ensure the user account has a password set (RDP requires password auth).

**Expected:** Remote Desktop is enabled. The Windows Defender Firewall
rule for Remote Desktop is automatically created.

---

### 9. Verify firewall allows RDP from WireGuard subnet

**Action:** In Windows Defender Firewall with Advanced Security:
1. Find the inbound rule for **Remote Desktop - User Mode (TCP-In)**.
2. Check its scope: it should allow connections from `Any` or specifically
   from `10.100.0.0/24`.

*(The default Windows rule allows RDP from any source; this is acceptable
since RDP is only reachable via the WireGuard interface, which is private.)*

**Expected:** RDP traffic from `10.100.0.0/24` is permitted.

---

### 10. Delete the transferred config file

**Action:** Delete the `.conf` file from the Windows machine (it contains the
WireGuard private key and is no longer needed after import).

**Expected:** File is deleted. The private key now lives only inside the
WireGuard tunnel service (protected by Windows).

---

### Part C: Verify from Operator's Machine

### 11. Verify WireGuard handshake

**Action:**
```bash
porthole status
```

**Expected:** `<node-name>` appears in the peer table with a handshake
timestamp within the last 2 minutes and non-zero Rx bytes.

---

### 12. Verify DNS resolution

**Action:**
```bash
ping <node-name>.wg
```

**Expected:** Ping resolves and returns replies from `10.100.0.N`.

---

### 13. Seed and verify Guacamole RDP connection

**Action:**
```bash
porthole seed-guac --apply
```
*(Or manually, until `--apply` is implemented — see RUNBOOK-001 Step 8.)*

**Expected:** A new RDP connection for `<node-name>` appears in Guacamole
(protocol: RDP, port 3389, hostname `10.100.0.N`).

**Action:** Open Guacamole in a browser from any enrolled node. Click the
`<node-name>` RDP connection. Enter the Windows username and password.

**Expected:** A Windows desktop session opens in the browser.

---

### 14. (No watchdog — note and mitigate)

**Known gap:** There is no automated watchdog for Windows peers (JOURNEY-003.PP-04 /
SPEC-005). The WireGuard client will reconnect on reboot if configured in
Step 7, but there is no automatic recovery from a dropped tunnel mid-session.

**Mitigation:** Ensure Step 7 is followed precisely (tunnel auto-start enabled).
If the family member reports loss of remote access, the operator can ask them to
restart the WireGuard tunnel: **System tray → WireGuard → Deactivate → Activate**.

Document the tunnel status page URL for this peer so the family member can
self-diagnose: `http://localhost:8888` (if the status server were installed —
currently not applicable to Windows peers).

## Teardown

To remove the Windows peer from the fleet:
1. On the operator's machine: `porthole remove <node-name> && porthole sync`
2. On the Windows machine: WireGuard → select tunnel → Remove

## Run Log

| Date | Executor | Result | Duration | Notes |
|------|----------|--------|----------|-------|
| 2026-03-04 | cristos | - | - | Runbook created |

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-04 | 031aaaa | Initial creation — Windows family machine enrollment |
