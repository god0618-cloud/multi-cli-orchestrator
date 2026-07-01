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

## v2.8

- Contributor-ready adapter scaffold output.
- Generated README, fake CLI fixture, and unittest contract template.
- Adapter contributor guide for promotion gates and review expectations.

## v3.0

- Public open-source MVP release baseline.
- README first-screen positioning for external users.
- Package metadata, release notes, and launch playbook.
- Source-tree and packaged template synchronization gate.

## v3.1

- Public walkthrough bundle.
- One-command demo output for README, replay transcript, dashboard, and adapter kit.
- Regression coverage for generated walkthrough artifacts.

## v3.2

- Static replay HTML output.
- Walkthrough bundles include text and HTML replay artifacts.
- Replay UI baseline before multi-worker execution.

## v3.3

- Adapter contributor CI harness.
- `mco adapter validate-kit` checks generated adapter kit health.
- Fail-fast guard against unsafe manifest promotion.

## v4.0

- Bounded multi-worker dispatch waves.
- `mco dispatch wave` queues one to six worker dispatches from a machine-readable spec.
- `mco dispatch wave --require-ready` applies adapter gates per worker and records blocked workers as evidence.
- Dispatch IDs include microseconds so batch dispatches to the same agent cannot overwrite each other.

## v4.1

- Dynamic workflow gates for task-local files, registered artifacts, ledger events, dispatch terminal state, and dispatch status counts.
- `mco workflow observe` as the safe loop-control readout.
- Automation recommendation states: `advance`, `wait`, `escalate`, and `complete`.
- Non-terminal dispatches force `wait`; blocked or failed dispatches force `escalate`.

## v4.2

- Stop-condition, max-round, and budget guardrails for bounded loop runners.
- Explicit user-decision gates and escalation artifacts.
- `mco workflow loop` for a hard-capped observe/advance cycle.

## v4.3

- Boss-view dashboard upgrade around workflow action, blockers, budget posture, and next owner.
- Dashboard `Workflow Loop Control` section showing current phase, recommended action, reason, and gate details.

## v4.4

- Expanded adapter capability matrix for interactive vs non-interactive execution across Claude Code, Kimi Code, Mimo Code, and CodeWhale-style CLIs.
- Matrix rows expose `execution_mode`, `automation_posture`, and `recommended_use` to avoid unsafe auto-dispatch assumptions.

## v4.5

- End-to-end validation run on a realistic product task before v5.0.
- `strict-self-closing` workflow template for plan -> execute -> verify -> close evidence loops.

## v5.0

- Strict-gate multi-CLI self-closing execution loop.
- Template-driven workflow execution with audit/replay evidence.
- Safe default posture: no infinite loops, no unbounded provider spend, no silent worker drift.
- First complete implementation target is the `strict-self-closing` template plus `workflow observe` / `workflow loop`.

## Future

- Wave execution policies after queue-time safety is proven.
- Real concurrent provider execution with quota and cancellation gates.
- Policy-driven escalation gates.
