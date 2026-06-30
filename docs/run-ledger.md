# Run Ledger

`RUN_LEDGER.json` is the replayable record of a task run.

Minimum schema:

```json
{
  "schema": "mco.run_ledger.v0.2",
  "run_id": "",
  "task_id": "",
  "request": "",
  "workflow": "",
  "loop_spec_ref": "",
  "sandbox_contract_refs": [],
  "events": [],
  "artifacts": [],
  "decisions": [],
  "rejected_branches": [],
  "final_verdict": ""
}
```

The run ledger is more important than a summary. Summaries can be wrong or incomplete; the ledger preserves enough structure to replay what happened.

Read-only replay:

```bash
mco run replay .mco-demo/tasks/<task_id>/RUN_LEDGER.json
mco run replay .mco-demo/tasks/<task_id>/RUN_LEDGER.json --json
```

The v0.5 replay command does not modify the ledger. It prints the timeline, registered artifacts, workflow, and final verdict so a user can inspect a run before trusting any summary.
