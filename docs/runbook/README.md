# Runbooks

Executable validation and operational procedures for the Porthole system. Runbooks bridge the gap between declarative specs ("did we build the right thing?") and operational confidence ("does the thing work when exercised?").

See `list-runbooks.md` for the full index.

## Artifact format

Each runbook lives in its own folder:

```
docs/runbook/(RUNBOOK-NNN)-<Title>/
  (RUNBOOK-NNN)-<Title>.md   — procedure definition, steps, and run log
```

## Phases

```
Draft → Active → Archived · Abandoned
```

## Executor modes

- **manual** — A human follows the steps.
- **agentic** — Claude Code executes the steps using available tools.
