# Loop Spec

`LOOP_SPEC.json` is mandatory for orchestrated work.

It answers:

- What is the goal?
- What inputs are allowed?
- What actions are allowed?
- What actions are forbidden?
- How will completion be verified?
- When should the loop stop?
- What evidence must be written?
- When must the system escalate to a human?

Minimum schema:

```json
{
  "schema": "mco.loop_spec.v0.2",
  "goal": "",
  "inputs": [],
  "allowed_actions": [],
  "forbidden_actions": [],
  "verification": [],
  "stop_condition": "",
  "evidence_to_write": [],
  "escalation_triggers": []
}
```

The loop spec exists to prevent vague autonomous execution. If the stop condition cannot be checked, the task is not ready for autonomous orchestration.

