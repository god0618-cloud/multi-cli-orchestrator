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

The baseline generic adapter includes:

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

The print-only Python path rejects imports, filesystem access markers, dynamic execution markers, subprocess access, sockets, and common module escape hatches.

v2.0 includes two real first-party prompt adapters:

```bash
mco adapter capabilities claude-code
mco adapter doctor claude-code --sandbox templates/sandbox-contracts/claude-code-supervised.json
mco adapter capabilities kimi-code
mco adapter doctor kimi-code --sandbox templates/sandbox-contracts/kimi-code-supervised.json
mco adapter scaffold kimi-code --output-dir adapter-kits/kimi-code
mco dispatch execute <task_id> <dispatch_id> \
  --agent claude-code \
  --sandbox <task-dir>/SANDBOX_CONTRACT.json \
  --prompt-file <task-dir>/prompt.md \
  --timeout-seconds 120 \
  --max-budget-usd 0.25
mco adapter smoke claude-code --workspace .mco-workspace --max-budget-usd 0.05
mco dispatch execute <task_id> <dispatch_id> \
  --agent kimi-code \
  --sandbox <task-dir>/SANDBOX_CONTRACT.json \
  --prompt-file <task-dir>/prompt.md \
  --timeout-seconds 120
mco adapter smoke kimi-code --workspace .mco-workspace
```

Claude Code execution is deliberately constrained:

- uses `claude --print`
- uses `--output-format json`
- uses `--no-session-persistence`
- uses `--permission-mode default`
- uses `--tools ""`
- requires a positive `--max-budget-usd` no greater than `1`
- requires `prompt-file` to live inside the task workspace
- writes `artifacts/<dispatch_id>-claude-execution-report.json`
- marks structured Claude errors, including `error_max_budget_usd`, as failed dispatches
- provides an explicit opt-in smoke command that creates a complete evidence bundle and verifies the fixed `MCO_ADAPTER_SMOKE_OK` sentinel

Kimi Code execution is deliberately constrained:

- uses `kimi --prompt`
- uses `--output-format text`
- requires `prompt-file` to live inside the task workspace
- writes `artifacts/<dispatch_id>-kimi-execution-report.json`
- provides an explicit opt-in smoke command that creates a complete evidence bundle and verifies the fixed `MCO_ADAPTER_SMOKE_OK` sentinel
- preserves quota as `unknown` because the current Kimi command contract does not expose a per-run budget cap equivalent to Claude Code's `--max-budget-usd`

New adapters should start with `mco adapter scaffold <agent>`. The scaffold is deliberately disabled by default and includes a manifest, sandbox draft, and smoke checklist. Promotion requires durable evidence for capability discovery, sandbox boundaries, quota semantics, non-interactive execution, execution reports, usage snapshots, and opt-in smoke gates.

Other first-party adapters for Mimo Code, CodeWhale, or additional CLIs remain disabled until they provide the same capability manifest, sandbox contract, quota checks, non-interactive command contract, and evidence reporter.
