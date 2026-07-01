# Release Notes v4.0.0

v4.0.0 introduces the first bounded multi-worker primitive for Multi-CLI Orchestrator: dispatch waves.

## Highlights

- `mco dispatch wave <task_id> --spec wave.json` queues a batch of worker dispatches from one machine-readable file.
- Waves are capped at six workers to keep coordination observable and reversible.
- `--require-ready` applies the same adapter gate used by single dispatches to every worker in the wave.
- Non-ready workers become blocked dispatch evidence and do not receive inbox files.
- A task-local wave manifest is written under `dispatch/waves/` for replay and audit.

## Safety Posture

v4.0.0 does not launch unconstrained real concurrent provider execution. It creates supervised, auditable wave dispatches first. Execution remains explicit and bounded through existing adapter execution commands.

## Compatibility

- Dispatch IDs now include microseconds to avoid collisions when multiple dispatches target the same agent in the same second.
- `generic-cli` now resolves its packaged sandbox contract correctly during doctor-backed adapter readiness checks.

## Verification

- Unit coverage for successful wave queueing.
- Unit coverage for blocked non-ready workers under `--require-ready`.
- Release checks remain expected before publication:
  - `python3 -m unittest tests.unit.test_workspace`
  - `python3 -m compileall -q src tests`
  - `PYTHONPATH=src python3 -m mco.cli release check . --json`
  - Public clone smoke.
