# Extraction Map

This document maps the private/local prototype surface into the open-source `mco` module plan.

The rule for v0.2 is: extract concepts and generic mechanics first, not private task data or machine-specific behavior.

## Source Prototype Surface

| Prototype Surface | Open-Source Module | v0.2 Action |
| --- | --- | --- |
| task create/current/submit/audit | `mco.task`, `mco.audit` | Reimplement generically; do not copy private paths |
| orchestrate-start | `mco.workflow`, `mco.dispatch` | Keep as roadmap; define objects first |
| dispatch inbox/claim/complete | `mco.dispatch` | Rebuild with generic file layout |
| adapter-capabilities | `mco.adapters` | Keep manifest concept; no local CLI assumptions |
| event-stream | `mco.replay`, `mco.dashboard` | Promote to run ledger and dashboard |
| LIVE_STATE/EVENT_STREAM HTML | `mco.dashboard` | Keep static dashboard concept |
| LOOP_SPEC | `mco.workflow` | Mandatory primitive |
| workflow templates | `templates/workflows` | Sanitize and rebuild examples |
| ecosystem/native memory watchers | optional governance plugin | Exclude from core v0.2 |
| KB governance bootstrap | optional governance profile | Exclude private paths; keep policy idea |

## Do Not Extract Directly

- Private task IDs.
- Local vault absolute paths.
- Hi拓一 business data.
- Native CLI memory/soul/profile files.
- Internal URLs, credentials, employee names, or store names.
- Any script whose default write target is outside the configured workspace.

## v0.2 Module Boundaries

```text
mco.config      workspace config and safe defaults
mco.schemas     loop spec, sandbox contract, run ledger schema helpers
mco.cli         command routing
mco.task        future task lifecycle
mco.workflow    future workflow DAG and loop validation
mco.dispatch    future inbox and baton passing
mco.adapters    future CLI capability manifests
mco.dashboard   future boss/control-room dashboard
mco.evidence    future artifact evidence registry
mco.audit       future safety and completion checks
mco.replay      future run ledger replay
```

## v0.2 Completion Standard

- `mco init` creates a clean workspace.
- `mco doctor` validates workspace readiness.
- `mco task create` creates generic task metadata, loop spec, and run ledger.
- `mco artifact register` records evidence in the run ledger.
- `mco dashboard` renders a static task dashboard.
- `mco audit` checks the tree for private-path and sensitive-pattern leakage.
- Loop spec and run ledger templates are generated.
- Private path scan passes.
- No private prototype behavior is copied into core.
