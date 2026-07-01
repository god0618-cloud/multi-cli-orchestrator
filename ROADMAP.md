# Roadmap

## v0.2

- Clean repository skeleton.
- Workspace config.
- `mco init`.
- `mco doctor`.
- `mco task create`.
- Static dashboard seed.
- Minimal safety audit.
- Bounded orchestration initializer.
- Loop spec and run ledger templates.
- Redaction checklist.

## v0.5

- Installable local MVP.
- Generic CLI adapter.
- Task lifecycle.
- Static dashboard.
- Hello multi-CLI demo.

## v0.8

- Sandbox contracts.
- Run replay MVP.
- Adapter readiness checks.
- Supervised dry-run dispatch execution.

## v1.0

- Safe command execution under sandbox gates.
- Execution evidence reports.
- Installable demo and replay.
- CI smoke gates.

## v1.1

- Git/release hygiene.
- Public documentation polish.
- Quota/usage preflight contract.
- First-party adapter manifests without default execution authority.
- Control-room dashboard improvements.

## v1.5

- First real supervised first-party adapter: Claude Code.
- Non-interactive prompt execution through `claude --print`.
- Host CLI auth preflight.
- Budget-limited execution.
- Transcript artifact registration.
- Structured budget/error fail-safe handling.

## v1.6

- Boss-view control room for task-local run state.
- Adapter readiness, dispatch counts, and budget surfaces.
- Clear escalation queue for owner decisions.
- Static dependency-free HTML output.

## v1.7

- Durable task-local usage snapshot contract.
- Per-agent observed cost and budget estimate rollups.
- Dashboard usage snapshot table.
- Explicit unknown-provider-quota semantics.

## v1.8

- Explicit real Claude Code adapter smoke command.
- Task-local smoke evidence bundle.
- Fixed sentinel verification.
- Cost-capped, opt-in adapter regression path.

## v1.9

- Adapter contributor scaffolding.
- Disabled-by-default onboarding files.
- Smoke checklist for future first-party adapters.
- Overwrite-safe adapter kit generation.

## v2.0

- Second supervised first-party adapter: Kimi Code.
- Multiple first-party adapter doctor/smoke paths.
- Shared task-local evidence contract across Claude Code and Kimi Code.
- Honest quota semantics per adapter: budget-limited where supported, unknown where unsupported.

## v2.1

- Adapter matrix and readiness boss view.
- Machine-readable comparison for implemented and disabled adapters.
- Optional local doctor probing.
- Promotion blockers for future adapters.

## v2.2

- Adapter readiness gate for auto-dispatch.
- `dispatch queue --require-ready`.
- Blocked-dispatch evidence for disabled or non-ready adapters.
- No inbox file for adapters that fail the gate.

## v2.3

- Adapter matrix embedded in task dashboard.
- Dispatch gate status embedded in task dashboard.
- Boss-view visibility for blocked auto-dispatches.

## v2.4

- Compact `mco status` operator command.
- Latest task, dispatch counts, latest dispatch, adapter readiness, quota semantics, and gate posture in one terminal readout.
- JSON output for scripts and optional audit counts for release/monitor loops.
- No implicit provider doctor probing during routine status checks.

## v2.5

- Explicit `mco status --doctor` probe mode.
- Machine-readable distinction between policy-baseline status and local adapter doctor checks.
- Doctor check counts and gate posture available in terminal and JSON output.
- Default status remains lightweight and non-probing.

## v2.6

- Bounded `mco monitor <task_id>` status snapshot loop.
- Task-local status snapshot artifacts registered in the run ledger.
- Hard cycle and interval caps to avoid accidental long-running daemons.
- Optional audit and doctor probing remain explicit per run.

## v2.7

- Workflow phase state in generated plans.
- `mco workflow status` for operator inspection.
- `mco workflow advance` for phase-gated pass/fail transitions.
- Fail-stop behavior and optional auto-dispatch to the next phase.

## Future

- Multi-worker supervised execution.
- Replay UI.
- Policy-driven escalation gates.
