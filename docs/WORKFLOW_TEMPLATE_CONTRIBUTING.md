# Workflow Template Contributing

Workflow templates define bounded task loops. They should make work easier to inspect, not easier to hide.

## Template Requirements

Each template must:

- use schema `mco.workflow.v0.2`,
- include a clear `name` and `description`,
- include a manifest when the workflow is intended for public reuse,
- define non-empty `phases`,
- give every phase `id`, `role`, `gates`, and `on_pass`,
- use machine-checkable gates,
- avoid vague gates such as "agent feels done",
- stop or escalate on missing evidence.

## Supported Gate Patterns

- `loop_spec_exists`
- `dashboard_exists`
- `artifact_registered:<label-or-filename>`
- `ledger_event:<event-type>`
- `user_decision:<decision-id>`
- `prototype_brief_exists`
- `plan_review_passed`
- `browser_visual_evidence_registered`
- `skill_evaluation_rubric_exists`
- `all_dispatches_terminal`
- `no_failed_dispatches`
- `no_blocked_dispatches`
- `dispatch_status_count:<status>:<minimum>`

## Public Manifest Guidance

Reusable templates should include:

- `trigger`
- `scope`
- `required_inputs`
- `artifacts`
- `verification`
- `stop_conditions`
- `failure_modes`
- `stack`
- `evidence_level`
- `budget`

Defaults should be friendly:

- `stack: single` unless the workflow truly needs two CLI workstations.
- `evidence_level: L1` unless the workflow is audit-heavy.
- token budget fields should describe when to defer detail into artifacts or workers.

## Add a Template

Add the same JSON file to both locations:

```text
templates/workflows/<name>.json
src/mco/templates/workflows/<name>.json
```

Then run:

```bash
PYTHONPATH=src python3 -m unittest tests.unit.test_workspace
PYTHONPATH=src python3 -m mco.cli release check . --json
PYTHONPATH=src python3 -m mco.cli audit .
```

## Dogfood It

At minimum:

```bash
mco init --workspace /tmp/mco-template-test
mco orchestrate-start "Template dogfood" \
  --template <name> \
  --workspace /tmp/mco-template-test
mco workflow observe <task_id> --workspace /tmp/mco-template-test
```

For real promotion, prove the workflow can reach a terminal recommendation:

- `complete` when evidence is present,
- `wait` when required evidence is missing,
- `escalate` when blocked/failed dispatches or user decision gates appear.

## Anti-Patterns

- Adding a phase with no meaningful gate.
- Using adapter execution as proof when an artifact gate would be safer.
- Hiding user decisions inside prose.
- Requiring real provider calls for basic template validation.
- Writing generated task workspaces into the repository root.
