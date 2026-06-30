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
