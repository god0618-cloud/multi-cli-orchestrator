# Release Notes v5.0.0

v5.0.0 turns Multi-CLI Orchestrator from bounded wave dispatch into a strict-gate self-closing loop.

## Highlights

- `mco workflow observe <task_id>` returns a machine-readable recommendation: `advance`, `wait`, `escalate`, or `complete`.
- `mco workflow loop <task_id> --max-steps N` runs a bounded observe/advance cycle. It is not a daemon and cannot run forever.
- Workflow gates now support task-local files, registered artifacts, ledger events, user decisions, dispatch terminal state, failed/blocked dispatch absence, and dispatch status counts.
- The dashboard now includes a `Workflow Loop Control` panel with current phase, recommended action, reason, and gate details.
- Adapter matrix rows now expose `execution_mode`, `automation_posture`, and `recommended_use`, making manual-only CLIs explicit.
- The new `strict-self-closing` workflow template models plan -> execute -> verify -> close with durable evidence gates.

## Safety Posture

v5.0.0 still does not launch unconstrained concurrent provider execution. A loop can only advance a phase when gates already pass, and it stops on missing evidence, blocked/failed dispatches, user-decision gates, completion, or the hard `--max-steps` cap.

## Workflow Gates

Supported gate forms include:

- `file_exists:<relative-path>`
- `artifact_registered:<label-or-filename>`
- `ledger_event:<event-type>`
- `user_decision:<decision-id>`
- `all_dispatches_terminal`
- `no_failed_dispatches`
- `no_blocked_dispatches`
- `dispatch_status_count:<status>:<minimum>`

## Verification

- Unit coverage for dynamic gate evaluation and workflow observe recommendations.
- Unit coverage for bounded loop stop behavior and user-decision escalation.
- Unit coverage for `strict-self-closing` completing only after implementation, verification, and close artifacts exist.
- Real CLI smoke of `strict-self-closing` through `mco workflow loop` reached `recommended_action=complete`.
- Release checks remain expected before publication:
  - `PYTHONPATH=src python3 -m unittest tests.unit.test_workspace`
  - `python3 -m compileall -q src tests`
  - `PYTHONPATH=src python3 -m mco.cli release check . --json`
