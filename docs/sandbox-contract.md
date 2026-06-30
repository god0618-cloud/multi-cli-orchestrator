# Sandbox Contract

`SANDBOX_CONTRACT.json` is required before parallel workers can start implementation work.

Minimum schema:

```json
{
  "schema": "mco.sandbox_contract.v0.2",
  "worker_id": "",
  "agent": "",
  "write_scope": [],
  "read_scope": [],
  "ports": [],
  "data_boundary": "",
  "credential_policy": "",
  "merge_owner": "",
  "verification_artifacts": []
}
```

The contract protects shared resources:

- files
- ports
- databases
- credentials
- dev servers
- auth state
- merge ownership

Parallel work without an explicit sandbox contract should fail closed.

v1.0 enforcement:

```bash
mco adapter doctor generic-cli --sandbox SANDBOX_CONTRACT.json
mco dispatch execute <task_id> <dispatch_id> --agent generic-cli --sandbox SANDBOX_CONTRACT.json --dry-run
mco dispatch execute <task_id> <dispatch_id> --agent generic-cli --sandbox SANDBOX_CONTRACT.json --command-json '["echo","hello"]'
```

The dry-run executor validates capability and sandbox gates, writes a dry-run evidence artifact, and records the result in `RUN_LEDGER.json`.

The safe-command executor also:

- runs with `cwd` locked to the task directory
- uses `shell=False`
- uses a minimal `PATH`
- enforces a timeout
- truncates stdout/stderr in the evidence report
- writes `artifacts/<dispatch_id>-execution-report.json`
- completes dispatches only on exit code `0`
- marks dispatches as `failed` on non-zero exit or timeout

Fail-closed behavior:

- no sandbox contract -> dispatch becomes `blocked`
- agent mismatch -> execution fails
- credential policy other than `no credentials` -> execution fails
- port access in generic dry-run -> execution fails
- write/read scope missing `task workspace only` -> execution fails
- command outside the allowlist -> execution fails
- unsafe print-only Python markers -> execution fails
