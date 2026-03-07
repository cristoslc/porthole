# Bug Index

## Reported

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [BUG-002](Reported/(BUG-002)-Prerequisites-Screen-Concurrent-Installs-And-Poor-UI.md) | Prerequisites screen: TUI should not be a package manager — delegate to ansible | TUI reimplements package management poorly; should delegate to an ansible playbook run by setup.sh. | 2026-03-06 | — |
| [BUG-003](Reported/(BUG-003)-Secrets-Screen-Porthole-Init-Fails-No-Interactive-Stdin.md) | Secrets screen: porthole init fails — no interactive stdin in async worker | `porthole init` needs interactive stdin but runs inside async worker where `suspend()` doesn't yield terminal. | 2026-03-07 | — |

## Abandoned

| ID | Title | Summary | Last Updated | Commit |
|----|-------|---------|--------------|--------|
| [BUG-001](Abandoned/(BUG-001)-TUI-Error-States-Opaque-and-Unrecoverable.md) | TUI Error States Opaque and Unrecoverable | Bootstrap TUI presented opaque pass/fail checks with no remediation path; abandoned as specious since bootstrap should install prereqs automatically. | 2026-03-05 | 7209b5b |
