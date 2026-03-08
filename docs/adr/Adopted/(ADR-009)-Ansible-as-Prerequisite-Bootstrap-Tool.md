---
title: "Ansible as Prerequisite Bootstrap Tool"
artifact: ADR-009
status: Adopted
author: cristos
created: 2026-03-07
last-updated: 2026-03-07
linked-epics:
  - EPIC-007
linked-specs:
  - SPEC-009
depends-on:
  - ADR-008
---

# ADR-009: Ansible as Prerequisite Bootstrap Tool

## Context

Porthole requires several tools on the operator's workstation before it can function: `nebula`, `nebula-cert`, `sops`, `age`, and `terraform`. The `porthole-setup` TUI needs a reliable, idempotent way to install all of them across Linux, macOS, and (eventually) Windows.

The question is whether porthole should install each tool directly (via scattered package manager calls, curl scripts, etc.) or delegate to a single tool that handles cross-platform package installation.

## Decision

**Ansible is the only tool porthole installs directly.** All other prerequisites are installed via an Ansible playbook.

The TUI's prerequisites screen:
1. Checks for Ansible and installs it if missing (pip or system package manager — the one direct install)
2. Runs a prerequisite playbook that ensures all other tools are present and at expected versions

## Alternatives Considered

### Direct package manager calls per tool
Each tool installed via platform-specific commands (`apt install`, `brew install`, `choco install`). This requires porthole to maintain per-platform install logic for every tool, handle version pinning, and deal with inconsistent package names across distributions. Fragile and duplicates what Ansible already does.

### Shell script installer
A `prereqs.sh` that detects the platform and installs everything. Simpler than scattering install logic through Python code, but still requires maintaining per-platform logic and lacks idempotency — re-running may reinstall or break existing versions.

### Container-based approach
Run porthole inside a container with all tools pre-installed. Eliminates the prerequisite problem entirely, but adds Docker as a hard dependency and complicates access to host resources (age keys, SSH keys, nebula service management).

## Consequences

**Positive:**
- Single, tested, idempotent install path per platform — Ansible playbooks are the same ones used for lighthouse provisioning (ADR-006), so the team already maintains them
- Version pinning and upgrade logic handled by Ansible's package modules
- Re-running the prerequisite playbook is safe (idempotent) — useful for "Re-check" in the TUI
- Ansible is already a project dependency for hub provisioning, so this adds no new tool category

**Accepted downsides:**
- Ansible itself must be installed without Ansible — this is the bootstrap problem, handled by a simple pip/package manager fallback
- Ansible installation adds ~30 seconds to first-run setup
- Operators who already have all tools installed still need Ansible present (though the playbook will no-op quickly)

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Adopted | 2026-03-07 | — | Extracted from DESIGN-002 design decision |
