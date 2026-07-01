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

Use `mco workflow status <task_id>` to inspect this state and `mco workflow advance <task_id>` to move the current phase forward. A failing verdict or failing gate puts the plan into `blocked` status.

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
