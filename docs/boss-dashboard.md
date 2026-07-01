# Boss Dashboard

The boss dashboard is the human-facing control room.

It should answer:

- Is user action required?
- Who is working?
- Who is waiting?
- What is blocked?
- What is the next baton?
- What evidence exists?
- What gates passed or failed?

v2.3 renders a static, dependency-free control room per task.

It reads only task-local evidence:

- `task.json`
- `RUN_LEDGER.json`
- `dispatch/dispatches/*.json`
- registered JSON artifacts, including Claude Code execution reports
- adapter matrix policy generated from packaged manifests/templates

The dashboard now includes:

- **Control Room**: task status, completed dispatch count, artifact count, and whether owner action is required.
- **Adapter Readiness**: one card per agent with dispatch counts, latest dispatch, latest execution summary, transcript label, observed budget, maximum budget, and approximate remaining budget.
- **Adapter Matrix**: policy baseline for known adapters, including readiness, supervision, quota status, smoke-gate availability, and promotion blockers. This section does not run provider doctor checks.
- **Dispatch Gate Status**: `--require-ready` gate evidence for auto-dispatch attempts, including blocked adapters and reasons.
- **Owner Escalations**: blocked/failed dispatches and structured adapter errors, or a clear “No owner action required” line.
- **Usage Snapshot**: per-agent observed cost, budget caps, remaining budget estimate, quota status, and last error from `USAGE_SNAPSHOT.json`.
- **Current Evidence**: latest run-ledger event.
- **Artifacts / Dispatches / Timeline**: audit trail details for deeper inspection.

This is intentionally still static HTML. The goal is operational legibility before a heavier UI: users can open a file, publish it as an artifact, or serve it with `mco serve` without installing a frontend stack.
