---
title: "Mixed-Provider Hub Provisioning"
artifact: STORY-001
status: Ready
author: cristos
created: 2026-03-03
last-updated: 2026-03-03
parent-epic: EPIC-007
depends-on: []
---

# Mixed-Provider Hub Provisioning

**As an** operator, **I want** to choose independent providers for compute and DNS when provisioning the hub, **so that** I can keep my existing DNS setup (Cloudflare, DigitalOcean, Hetzner, etc.) without migrating it just to spin up a server elsewhere.

## Acceptance Criteria

1. The hub spinup TUI presents separate selectors for compute provider (Hetzner / DigitalOcean) and DNS provider (Cloudflare / DigitalOcean / Hetzner / none).
2. Terraform activates only the DNS module matching the selected `dns_provider` variable; tokens for unselected providers are not required and not validated.
3. Setting `dns_provider = "none"` provisions the server without creating any DNS record (the operator manages DNS manually or out-of-band).
4. If a provider-specific token env var is already set in the environment (e.g. `CLOUDFLARE_API_TOKEN`, `TF_VAR_do_token`), the TUI pre-selects the matching DNS provider and pre-fills the token field.
5. `terraform init` and `terraform plan` succeed regardless of which `dns_provider` value is selected, as long as the matching token is supplied.

## Lifecycle

| Phase | Date | Commit | Notes |
|-------|------|--------|-------|
| Draft | 2026-03-03 | 269e517 | Initial creation |
