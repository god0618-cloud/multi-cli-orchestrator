# Workflow Schema

Workflow schema v0.2 is a minimal DAG-like phase list with:

- optional manifest
- role
- preferred agent
- inputs
- outputs
- gates
- on-pass transition
- on-fail transition
- user decision gates

No worker should start a phase unless required inputs and gates are satisfied.

## Manifest

Workflow templates may include a `manifest` block. The manifest is the operator-facing contract that explains when the workflow should be used, what inputs it needs, which evidence artifacts it will produce, and where it must stop instead of pretending to continue.

Required manifest fields:

| Field | Meaning |
| --- | --- |
| `trigger` | The situation that should activate this workflow |
| `scope` | What the workflow covers and what it intentionally does not cover |
| `required_inputs` | Inputs the first owner must clarify before worker fanout |
| `artifacts` | Durable outputs expected across the loop |
| `verification` | Evidence and gates that prove the workflow is complete |
| `stop_conditions` | Conditions that must pause or escalate the loop |
| `failure_modes` | Common ways this workflow can produce misleading progress |
| `plan_review_required` | Optional boolean; when true, fanout should wait for review |
| `fanout_policy` | Optional machine-readable worker fanout limits |
| `stack` | Optional `single` or `dual`; default design posture should be `single` |
| `evidence_level` | Optional `L1`, `L2`, or `L3`; default should be `L1` |
| `budget` | Optional token budget with `avg_token_cost`, `hard_cap`, and `defer_policy` |

The manifest is copied into `plan.json` by `mco orchestrate-start`, so dashboards and future automation can explain not only the current phase but also the workflow's intent.

### Evidence Levels

| Level | Intended Use | Minimum Evidence |
| --- | --- | --- |
| `L1` | Default local workflow | Final-state screenshot or compact browser/visual evidence manifest |
| `L2` | Reviewable product work | Actions log plus screenshots or state notes |
| `L3` | Audit-heavy work | Actions log, screenshots or recording, and explicit final-state assertions |

Use the lowest level that proves the claim. Raising the evidence level should be a review decision, not a default tax on every user.

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
| `prototype_brief_exists` | `prototype-brief.md` is registered as a task artifact |
| `plan_review_passed` | `plan-review-report.md` is registered and a `plan_review_passed` ledger event exists |
| `browser_visual_evidence_registered` | `browser-visual-evidence.json` is registered as a task artifact |
| `skill_evaluation_rubric_exists` | `skill-evaluation-rubric.md` is registered as a task artifact |
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
