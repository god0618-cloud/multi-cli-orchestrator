# Workflow Schema

Workflow schema v0.2 is a minimal DAG-like phase list with:

- role
- preferred agent
- inputs
- outputs
- gates
- on-pass transition
- on-fail transition
- user decision gates

No worker should start a phase unless required inputs and gates are satisfied.

v2.7 generated plans also include runtime phase state:

- `current_phase`
- `phase_states.<phase_id>.status`
- `phase_states.<phase_id>.gate_results`
- `phase_states.<phase_id>.summary`

Use `mco workflow status <task_id>` to inspect this state, `mco workflow observe <task_id>` to get a machine-readable next-action recommendation, and `mco workflow advance <task_id>` to move the current phase forward. A failing verdict or failing gate puts the plan into `blocked` status.

## Gate vocabulary

v4.1 gates are intentionally small and evidence-oriented. They are evaluated against the task directory, dispatch records, and `RUN_LEDGER.json`.

| Gate | Meaning |
| --- | --- |
| `loop_spec_exists` | `LOOP_SPEC.json` exists |
| `run_ledger_has_events` | `RUN_LEDGER.json` has at least one event |
| `dashboard_exists` | `dashboard.html` exists |
| `sandbox_contract_not_required_for_single_worker` | Compatibility gate for the single-worker demo |
| `file_exists:<relative-path>` | A task-local file exists |
| `artifact_registered:<label-or-filename>` | A run-ledger artifact label or filename exists |
| `ledger_event:<event-type>` | At least one run-ledger event of that type exists |
| `user_decision:<decision-id>` | A run-ledger decision with this id has `status=approved` |
| `all_dispatches_terminal` | No dispatch is still `queued` or `claimed` |
| `no_failed_dispatches` | No dispatch has `status=failed` |
| `no_blocked_dispatches` | No dispatch has `status=blocked` |
| `dispatch_status_count:<status>:<minimum>` | At least `<minimum>` dispatches have the requested status |

## Observe contract

`mco workflow observe <task_id>` returns:

- `recommended_action=advance` when the current phase gates pass and no worker is still running.
- `recommended_action=wait` when required evidence is missing or dispatches are still `queued` / `claimed`.
- `recommended_action=escalate` when the workflow is blocked or a dispatch is `blocked` / `failed`.
- `recommended_action=complete` when the workflow has completed.

This is the safe loop-control surface for automation. A loop runner should call `observe`, then only call `advance` when the recommendation is `advance`.

`mco workflow loop <task_id>` implements that pattern with a hard step cap. It is not a daemon and it does not execute external CLIs by itself. It only advances already-satisfied workflow phases and optionally queues the next dispatch through normal adapter gates.

Minimal template:

```json
{
  "schema": "mco.workflow.v0.2",
  "name": "hello-multi-cli",
  "phases": [
    {
      "id": "plan",
      "role": "planner",
      "gates": ["loop_spec_exists"],
      "outputs": ["plan.json"],
      "on_pass": "evidence",
      "on_fail": "human_review"
    }
  ]
}
```

Strict self-closing template:

```bash
mco orchestrate-start "Product task" --template strict-self-closing --workspace .mco-workspace
mco workflow loop "$TASK_ID" --workspace .mco-workspace --max-steps 1
```

`strict-self-closing` models the v5.0 target loop:

1. `plan` passes only when `LOOP_SPEC.json` exists.
2. `execute` waits for `implementation-report.md`, terminal dispatches, and zero failed/blocked dispatches.
3. `verify` waits for `verification-report.md`, a `verification` ledger event, and `dashboard.html`.
4. `close` waits for `close-report.md` and clean dispatch state before completing.
