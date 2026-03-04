---
title: "Node Bootstrap TUI"
artifact: SPEC-009
status: Approved
author: cristos
created: 2026-03-03
last-updated: 2026-03-04
parent-epic: EPIC-007
linked-research: []
linked-adrs:
  - ADR-006
depends-on:
  - SPEC-008
addresses:
  - JOURNEY-001.PP-01
  - JOURNEY-001.PP-02
  - JOURNEY-001.PP-03
  - JOURNEY-002.PP-01
  - JOURNEY-002.PP-02
  - JOURNEY-002.PP-04
  - JOURNEY-004.PP-02
---

# SPEC-009: Node Bootstrap TUI

**Status:** Approved
**Author:** cristos
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Parent Epic:** [EPIC-007](../../../epic/Proposed/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap/(EPIC-007)-Zero-Touch-Hub-Provisioning-and-Node-Bootstrap.md)

### Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft    | 2026-03-03 | 2ec07f7 | Initial creation |
| Approved | 2026-03-04 | 62f5522 | Enrollment, service_install, hub_check screens implemented; summary + --check pending |

---

## Problem Statement

Enrolling a new node in the fleet today requires the operator to:

1. Know to run `porthole add`, `porthole sync`, and `porthole gen-peer-scripts`.
2. Manually install the generated service files on the correct paths.
3. Install WireGuard, SOPS, age, and the porthole package beforehand.
4. Have the age key and `network.sops.yaml` already in place.

There is no single entry point. There is no guidance for what to do if the hub
is not yet up. There is no path for a family member (or for the operator on a
fresh machine) to go from zero to enrolled without reading documentation.

This spec defines a `setup.sh` entry point and a Textual TUI that guides the
user through the full enrollment flow — idempotently, interactively, and
without assuming prior knowledge of the underlying tools.

## External Behavior

### Entry point

```
./setup.sh
```

`setup.sh` is a bash shim. It:
1. Checks for `uv`; installs it if missing (via the official installer).
2. Runs the Textual TUI: `uv run python -m porthole_setup`.
3. Passes through any CLI flags to the TUI for non-interactive or CI use.

### Platform support

| Platform | Status |
|----------|--------|
| Linux Mint 22 (Cinnamon/X11) | Supported |
| macOS (Sonoma+) | Supported |
| Other Linux distros | Best-effort (apt-based assumed) |
| Windows | Out of scope |

### TUI flows

The TUI is a Textual app organized into screens. The user moves forward (or
skips steps that are already done). On re-runs, completed steps are shown as
already-done with a skip option.

#### Flow 1: Prerequisites

Checks and installs:

| Tool | Linux | macOS |
|------|-------|-------|
| `uv` | Official installer | Official installer |
| `wireguard-tools` | `apt install wireguard` | `brew install wireguard-tools` |
| `sops` | GitHub release download | `brew install sops` |
| `age` | GitHub release download | `brew install age` |
| `porthole` | `uv tool install <path or PyPI>` | Same |
| `terraform` | HashiCorp APT repo | `brew install terraform` |
| `ansible` | `pipx install ansible` via uv | Same |

Each tool is checked first (`which <tool>`). If already present and the version
is adequate, the step is skipped and shown as complete.

#### Flow 2: Secrets

| Step | Logic |
|------|-------|
| Age key | Check `~/.config/sops/age/keys.txt`. If absent: offer two paths — (a) **Generate new key** (for first-time setup on this machine as operator), or (b) **Transfer key from another machine** — show the exact `scp` command the operator can run on an already-enrolled machine to copy their key to this one, then re-check (addresses JOURNEY-002.PP-01). If present, show public key and offer to regenerate (with warning). |
| `.sops.yaml` | Check for `.sops.yaml` in repo root. If absent, write from age public key. |
| `network.sops.yaml` | Check for state file. If absent, prompt for hub endpoint and run `porthole init`. If present, load and display summary (peer count, endpoint). Offer to re-initialize (destructive, requires confirmation). |

#### Flow 3: Hub check

1. Parse hub endpoint from `network.sops.yaml`.
2. Attempt to reach the hub: ping the public endpoint, then attempt a
   WireGuard handshake (`wg show`) if WireGuard is already configured.
3. If hub is reachable: show status, skip to Flow 4.
4. If hub is not reachable: display status and offer two options:
   - **Spin up hub** — runs Terraform + Ansible (requires cloud credentials;
     TUI prompts for them or reads from environment). See Hub Spinup sub-flow.
   - **Skip** — continue without a hub (service files will be installed but
     WireGuard will not connect until the hub is available).

**Hub Spinup sub-flow:**

1. **Pre-flight summary**: Before showing the credentials form, display a
   summary panel listing exactly which tokens and environment variables are
   needed for the selected provider combination. This gives the operator a
   chance to prepare before the form is shown (addresses JOURNEY-001.PP-01).
2. **Provider selection**: Compute provider (Hetzner / DigitalOcean) and DNS
   provider (None / Cloudflare / DigitalOcean / Hetzner DNS) are separate
   selectors. Tokens for unselected providers are not required.
3. **Token pre-fill**: If provider-specific env vars are already set
   (e.g., `HCLOUD_TOKEN`, `CLOUDFLARE_API_TOKEN`), pre-fill the
   corresponding fields and pre-select the matching providers.
4. **Endpoint handling**: The hub hostname is pre-filled from
   `network.sops.yaml`. If the operator has not yet run `porthole init`
   (first-time setup), the TUI accepts a placeholder hostname and offers to
   update the endpoint in `network.sops.yaml` after `terraform output hub_ip`
   confirms the server is live (addresses JOURNEY-001.PP-02).
5. **Execution sequence**: `terraform init` → `terraform apply -auto-approve`
   → `terraform output -raw hub_ip` → `ansible-playbook site.yml -e hub_ip=…`.
   All output streams live into the TUI RichLog.
6. **Post-deploy sync**: After Ansible completes successfully, the TUI
   automatically runs `porthole sync` to push the current peer configs to the
   new hub. This ensures any peers already registered in state are enrolled on
   the new hub immediately (addresses JOURNEY-001.PP-03 / JOURNEY-004.PP-02).
7. On success, return to Hub Check. The re-check should show the hub as
   reachable.

#### Flow 4: Node enrollment

1. Check if this node is already registered in `network.sops.yaml`
   (by matching the current machine's hostname or a name the operator provides).
2. If not registered: prompt for node name, role (workstation / server / family),
   and platform (linux / macos / windows). Run `porthole add <name> --role <role>
   --platform <platform>`, then `porthole sync`.
3. If already registered: show registration details, offer to re-sync
   (`porthole sync`).
4. Run `porthole gen-peer-scripts <name> --out peer-scripts/<name>/`.
5. Install service files via `porthole install-peer <name>` (addresses
   JOURNEY-002.PP-04 — this CLI command must exist; see SPEC-003 for its
   definition):
   - **Linux:** copies scripts to system paths, runs `systemctl daemon-reload`,
     enables and starts watchdog timer, tunnel service, and status server.
   - **macOS:** copies plists to `/Library/LaunchDaemons/`, runs
     `launchctl load -w` for each.
6. Apply the local WireGuard config and bring the interface up.
7. Show final status: WireGuard interface up, hub ping result, status server URL.

Notes:
- This flow runs on the machine being enrolled. The operator must have write
  access to `/etc/wireguard/` and `/etc/systemd/system/` (Linux) or
  `/Library/LaunchDaemons/` (macOS) — `sudo` is required.
- The TUI should handle `sudo` prompts gracefully (e.g., prompt for password
  in the TUI itself, or show a pre-flight warning that the operator will be
  prompted for their password).

### Idempotency

Every step checks current state before acting. Running `./setup.sh` on a
machine that is already fully enrolled should:
- Show all steps as already complete.
- Offer a "re-sync" option to push config updates.
- Make no changes unless the user explicitly selects an action.

### Secret regeneration

The TUI offers regeneration explicitly:
- Age key regeneration: warns that this will break decryption of existing state.
- Network state re-initialization: warns that this will require re-enrolling all nodes.
- Both require a typed confirmation (`yes`) before proceeding.

## Acceptance Criteria

- **Given** a fresh Linux Mint or macOS machine with no tools installed,
  **when** `./setup.sh` is run and the user completes all flows,
  **then** the node is enrolled in the fleet, WireGuard is active, and
  `ping hub.wg` succeeds.

- **Given** an already-enrolled machine,
  **when** `./setup.sh` is run,
  **then** no changes are made unless the user selects an action, and the
  process exits cleanly.

- **Given** an enrolled machine where the hub is not reachable,
  **when** the user selects "Spin up hub" and cloud credentials are in the
  environment,
  **then** Terraform provisions a VPS and Ansible configures it, and the hub
  becomes reachable at the configured endpoint.

- **Given** a machine where `network.sops.yaml` exists but the age key is absent,
  **when** `./setup.sh` is run,
  **then** the TUI detects the mismatch, explains it, and offers recovery options:
  (a) transfer key from another machine (shows `scp` command), or
  (b) generate new key + re-initialize state.

- **Given** a hub that has just been spun up via the TUI (Terraform + Ansible
  complete),
  **when** the Ansible playbook finishes successfully,
  **then** the TUI automatically runs `porthole sync` and shows its output before
  returning to Hub Check.

- **Given** a hub spinup where the compute and DNS providers require different API
  tokens,
  **when** the operator reaches the Hub Spinup screen,
  **then** a pre-flight panel lists exactly which environment variables and tokens
  are required for the selected provider combination, before the credentials form
  is shown.

- **Given** `./setup.sh --check` (non-interactive flag),
  **then** the TUI prints a status summary and exits 0 if all steps are complete,
  or exits 1 with a list of incomplete steps.

## Scope & Constraints

**In scope:**
- Linux Mint and macOS.
- Interactive (Textual TUI) and non-interactive (`--check`) modes.
- All prerequisite installation, secret management, hub check, enrollment, and
  service file installation flows.
- `setup.sh` bash shim.

**Not in scope:**
- Windows.
- Unattended/fully non-interactive CI enrollment (a future concern).
- Guacamole client configuration on the node (Guacamole runs on the hub, not nodes).
- Node removal or de-enrollment via the TUI (use `porthole remove` directly).

## Implementation Approach

```
setup.sh                     Bash shim: ensure uv, then uv run python -m porthole_setup
src/porthole_setup/
  __main__.py                Entry point: parse flags, launch Textual app
  app.py                     Textual App subclass, screen routing
  screens/
    prerequisites.py         Check/install each tool; show progress
    secrets.py               Age key + .sops.yaml + network.sops.yaml management
    hub_check.py             Ping hub; offer spin-up or skip
    hub_spinup.py            Prompt cloud creds; run terraform + ansible subprocess
    enrollment.py            porthole add + sync + gen-peer-scripts
    service_install.py       Install systemd (Linux) or LaunchDaemons (macOS) files
    summary.py               Final status: all green or list of issues
  platform.py                Detect Linux/macOS; dispatch installation commands
  state.py                   Read network.sops.yaml via subprocess sops -d
  runner.py                  Subprocess wrapper with live output in Textual widget
```

Textual dependency is added to `pyproject.toml`. The app is invoked via
`uv run python -m porthole_setup`, keeping the Python environment fully managed
by uv and requiring no system Python.
