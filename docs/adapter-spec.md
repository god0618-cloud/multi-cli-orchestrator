# Adapter Spec

Adapters describe how an external CLI workstation participates in a task.

Planned manifest fields:

```json
{
  "agent": "",
  "adapter_type": "",
  "interactive": false,
  "non_interactive": false,
  "supervised": false,
  "can_read_inbox": false,
  "can_write_artifacts": false,
  "can_run_shell": true,
  "can_use_browser": false,
  "quota_status": "unknown"
}
```

The orchestrator should use adapter capability evidence, not assumptions.

v1.0 includes only:

```bash
mco adapter capabilities generic-cli
mco adapter doctor generic-cli --sandbox SANDBOX_CONTRACT.json
mco dispatch execute <task_id> <dispatch_id> --agent generic-cli --sandbox SANDBOX_CONTRACT.json --command-json '["echo","hello"]'
```

Readiness states:

- `READY_SUPERVISED`: capability manifest and sandbox contract both pass.
- `READY_MANUAL`: adapter is known, but no sandbox contract was provided.
- `BLOCKED`: manifest or sandbox contract failed.

`generic-cli` remains a supervised generic adapter. It does not run arbitrary shell commands.

The v1.0 execution surface is intentionally narrow:

- `echo ...`
- `python -c "print(...)"`, resolved through the current Python interpreter

The print-only Python path rejects imports, filesystem access markers, dynamic execution markers, subprocess access, sockets, and common module escape hatches. Real first-party adapters for Claude Code, Kimi Code, Mimo Code, CodeWhale, or other CLIs should be added only after they provide their own capability manifest, sandbox contract, quota checks, and evidence reporter.
