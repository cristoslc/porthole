---
title: "Porthole Setup TUI"
artifact: DESIGN-002
status: Draft
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
superseded-by:
linked-epics:
  - EPIC-007
linked-stories: []
linked-specs:
  - SPEC-009
linked-bugs: []
linked-adrs:
  - ADR-008
  - ADR-006
depends-on:
  - ADR-008
  - DESIGN-001
---

# DESIGN-002: Porthole Setup TUI

## Interaction Surface

The `porthole-setup` TUI — a 7-screen wizard that walks a new operator through first-time network setup and node enrollment. Built with Textual, launched via the `setup.sh` bash shim.

**Scope:** The TUI screen flow, screen states, and user interactions. Not the CLI commands the TUI invokes (DESIGN-001), not system internals (Spec), not hub infrastructure (SPEC-008).

## Screen Flow

```
┌──────────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐
│ Prerequisites├───→│ Secrets  ├───→│ Hub Check ├───→│ Hub Spinup │
└──────────────┘    └──────────┘    └─────┬─────┘    └──────┬─────┘
                                          │                 │
                                          │  (hub exists)   │
                                          ▼                 ▼
                                    ┌────────────┐    ┌───────────┐    ┌─────────┐
                                    │ Enrollment ├───→│ Service   ├───→│ Summary │
                                    │            │    │ Install   │    │         │
                                    └────────────┘    └───────────┘    └─────────┘
```

Every screen supports "Back" navigation to the previous screen. "Continue" advances to the next screen. Screens gate progression — the operator cannot skip ahead past a screen with unmet requirements.

## Screen 1: Prerequisites

All tools are required. This screen bootstraps Ansible (the only direct install), then uses Ansible to ensure everything else is in place.

**Flow:**

1. **Check for Ansible.** If missing, install it directly (pip or package manager — the one tool porthole installs itself).
2. **Run prerequisite playbook.** Ansible ensures the remaining tools are installed and at the expected versions:

| Tool | Purpose |
|------|---------|
| `nebula` | Overlay network binary |
| `nebula-cert` | Certificate management (bundled with nebula) |
| `sops` | Secrets encryption |
| `age` | Encryption backend for SOPS |
| `terraform` | VPS provisioning |

3. **Display results.** Show a checklist of all tools with version and status (installed / failed). All must pass to continue.

**States:**
- **Initial:** Checklist with unknown status for each tool. "Install" button prominent.
- **Installing:** Progress output streamed from Ansible. Buttons disabled.
- **All passed:** Green checkmarks on all tools. "Continue" enabled.
- **Partial failure:** Red X on failed tools with error detail. "Install" available to retry. "Continue" disabled.

**Actions:** "Install" (runs the bootstrap), "Re-check", "Continue" (enabled when all pass), "Back".

## Screen 2: Secrets

Generates the age keypair used by SOPS for encrypting `network.sops.yaml`.

**Flow:**

1. Check for existing age key at the expected path
2. If none exists, generate one
3. Write `.sops.yaml` config pointing to the age public key
4. Display the age public key for the operator to record

**States:**
- **No key:** "Generate" button. Public key display area empty.
- **Key exists:** Green checkmark, public key displayed. "Continue" enabled.

**Actions:** "Generate", "Continue", "Back".

## Screen 3: Hub Check

Determines whether the network has been initialized and the lighthouse is reachable.

**Flow:**

1. Check for `network.sops.yaml`
2. If present, attempt DNS resolution of the lighthouse endpoint (informational)
3. Display status and offer next steps

**States:**
- **No state file:** Show endpoint input field + "Initialize" button. Runs `porthole init --endpoint <endpoint> --age-key <key>` to create CA + lighthouse cert + encrypted state.
- **State exists, lighthouse unreachable:** Show DNS resolution status (informational). Offer "Spin Up Hub" (→ Screen 4) or "Continue" (skip provisioning if lighthouse is managed externally).
- **State exists, lighthouse reachable:** Green status. "Continue" to enrollment.

**Actions:** "Initialize", "Spin Up Hub", "Re-check", "Continue", "Back".

## Screen 4: Hub Spinup

Provisions the lighthouse on a VPS. Runs two stages with live output.

**Flow:**

1. **Terraform:** `terraform apply` — creates VPS, configures DNS, opens firewall
2. **Ansible:** `ansible-playbook` — installs nebula lighthouse, CoreDNS, Guacamole Docker stack

Cloud-init injects the lighthouse config at first boot. Progress is streamed to the TUI.

**States:**
- **Ready:** "Spin Up" button. Summary of what will be provisioned.
- **Running:** Live output stream from Terraform and Ansible. Buttons disabled except "Back" (with confirmation — cancels provisioning).
- **Complete:** Green status showing lighthouse endpoint and IP. "Continue" enabled.
- **Failed:** Error output displayed. "Retry" available.

**Actions:** "Spin Up", "Retry", "Continue", "Back".

## Screen 5: Enrollment

Enrolls the current machine as a peer in the network.

**Flow:**

1. Prompt for node name, role, and platform (pre-filled where detectable)
2. Run `porthole add <name> --role <role> --platform <platform>` — signs cert, allocates IP
3. Run `porthole peer-config <name>` — renders config bundle
4. Display assigned IP and confirmation

The lighthouse discovers this node automatically when nebula starts — no hub config push needed.

**States:**
- **Input:** Name field (required), role dropdown (workstation/server/family), platform dropdown (linux/macos/windows, auto-detected). "Enroll" button.
- **Enrolling:** Progress output. Buttons disabled.
- **Complete:** Assigned IP, role, and groups displayed. "Continue" enabled.
- **Already enrolled:** If this machine's hostname is already in state, show existing enrollment details. Offer "Re-enroll" (with `--force`) or "Continue".

**Actions:** "Enroll", "Re-enroll", "Continue", "Back".

## Screen 6: Service Install

Installs the nebula service on the current machine.

**Flow:**

1. Copy config bundle to the platform's nebula config directory
2. Generate and install the platform-appropriate service unit
3. Enable and start the nebula service
4. Verify tunnel connectivity (ping lighthouse overlay IP)

| Platform | Config directory | Service type |
|----------|-----------------|-------------|
| Linux | `/etc/nebula/` | systemd unit |
| macOS | `/etc/nebula/` | launchd plist |
| Windows | `C:\Program Files\Nebula\` | Windows service |

One service (`nebula`) per node. Nebula handles reconnection natively via `punchy` — no watchdog timer required for basic connectivity. An optional SSH tunnel service (SPIKE-006 Layer 2) is available as an add-on for reverse access fallback.

**States:**
- **Ready:** "Install" button. Summary of what will be installed and where.
- **Installing:** Progress output from file copy, service enable, connectivity check.
- **Connected:** Green status — tunnel active, lighthouse reachable over overlay. "Continue" enabled.
- **Installed but no connectivity:** Amber status — service running but lighthouse not reachable. Hint: "Lighthouse may not be provisioned yet." "Continue" enabled (connectivity is verified but not gated).

**Actions:** "Install", "Re-check", "Continue", "Back".

## Screen 7: Summary

Displays a checklist of completed setup steps with final status.

- [x] Prerequisites installed
- [x] Age key generated and SOPS configured
- [x] Network initialized (CA created)
- [x] Lighthouse provisioned and reachable
- [x] This node enrolled (certificate signed)
- [x] Nebula service running (tunnel active)

Shows the node's overlay IP, assigned groups, and lighthouse endpoint.

**Actions:** "Finish" (exits the TUI).

## Frameworks and Tools

| Component | Tool | Notes |
|-----------|------|-------|
| TUI framework | Textual | Python TUI with screen-based navigation |
| Entry point | `setup.sh` | Bash shim that launches the TUI |
| Bootstrap tool | Ansible | The one tool installed directly; installs all other prerequisites |
| CLI backend | `porthole` CLI | TUI invokes CLI commands (DESIGN-001) for init, add, peer-config, bootstrap |

## Edge Cases and Error States

### Ansible not installable
If Ansible cannot be installed (no pip, no package manager access), the prerequisites screen shows an error with manual install instructions. The TUI cannot proceed without Ansible.

### Prerequisite playbook fails partially
Individual tool failures are shown with error output. The operator can fix the issue externally and "Re-check", or retry "Install" to re-run the full playbook (Ansible is idempotent).

### Hub spinup interrupted
If the operator navigates back during provisioning, a confirmation dialog warns that Terraform may leave partial infrastructure. Partial state can be cleaned up by re-running the spinup (Terraform is idempotent).

### Network already initialized
If `network.sops.yaml` exists when reaching the hub check screen, the TUI skips initialization and shows current state. The operator can "Re-initialize" only through the CLI (`porthole init --force`) — the TUI does not offer destructive re-initialization.

### Machine already enrolled
If the current hostname matches an existing peer in state, the enrollment screen shows the existing entry and offers "Re-enroll" (which runs `porthole add --force` to re-sign the certificate) or "Continue" to skip.

## Design Decisions

1. **Ansible as bootstrap tool.** Ansible is the only tool porthole installs directly. All other prerequisites are installed via an Ansible playbook. This gives a single, tested, idempotent install path per platform instead of scattered package manager calls.

2. **TUI invokes CLI commands.** The TUI is a guided wrapper around `porthole` CLI commands, not a parallel implementation. `porthole init`, `porthole add`, `porthole peer-config`, and `porthole bootstrap` are the same commands the operator would run manually. This keeps behavior consistent and testable.

3. **Linear screen progression with back-navigation.** Screens gate forward progression (can't enroll without prerequisites, can't install service without enrollment) but allow back-navigation. This prevents operators from reaching screens with unmet dependencies while allowing corrections.

4. **Hub spinup is optional.** If the lighthouse is managed externally (pre-existing VPS, different provisioning tool), the operator skips the spinup screen. The TUI adapts to this by checking lighthouse reachability, not provisioning status.

5. **Connectivity check is informational, not gating.** The service install screen verifies tunnel connectivity but does not block progression if the lighthouse is unreachable. The operator may be setting up the workstation before the lighthouse is provisioned.

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-07 | — | Split from DESIGN-001 to separate CLI and TUI concerns |
