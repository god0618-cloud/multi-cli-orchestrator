# Command Reference

Command surface:

| Command | Purpose |
| --- | --- |
| `mco init` | Initialize a local workspace |
| `mco doctor` | Validate workspace readiness |
| `mco task create` | Create a task with `task.json`, `LOOP_SPEC.json`, and `RUN_LEDGER.json` |
| `mco task create --json` | Create a task and print machine-readable paths |
| `mco task list` | List workspace tasks |
| `mco task status` | Show task metadata |
| `mco task event` | Append an event to `RUN_LEDGER.json` |
| `mco artifact register` | Register evidence in the run ledger |
| `mco adapter capabilities` | Show adapter capability manifest for `generic-cli` or `claude-code` |
| `mco adapter doctor` | Check adapter readiness against optional sandbox contract |
| `mco adapter smoke` | Run an explicit opt-in real Claude Code adapter smoke test |
| `mco dispatch queue` | Queue a dispatch for an agent |
| `mco dispatch list` | List task dispatches |
| `mco dispatch claim` | Claim a queued dispatch |
| `mco dispatch complete` | Complete a dispatch |
| `mco dispatch execute` | Validate adapter/sandbox gates, dry-run, run a safe command, or run a bounded Claude Code prompt |
| `mco dashboard` | Render a static task dashboard |
| `mco usage snapshot` | Write a task-local usage/quota evidence snapshot |
| `mco orchestrate-start` | Create a task and initialize a workflow plan |
| `mco schema validate` | Validate loop spec, adapter manifest, sandbox contract, or run ledger |
| `mco serve` | Serve a workspace directory over HTTP |
| `mco audit` | Run minimal safety audit |
| `mco demo hello-multi-cli` | Run sanitized built-in demo |
| `mco run replay` | Print a read-only timeline from `RUN_LEDGER.json` |
| `mco release check` | Run release readiness checks |

`mco dispatch execute --dry-run` validates gates and writes evidence only.

`mco dispatch execute --command-json '["echo","hello"]'` runs a narrowly allowed command after sandbox enforcement. It is not an arbitrary shell runner.

`mco dispatch execute --agent claude-code --prompt-file <task-dir>/prompt.md --max-budget-usd 0.25` runs a supervised Claude Code prompt through `claude --print` with tools disabled, session persistence disabled, timeout/output limits, and a transcript artifact.

`mco adapter smoke claude-code --workspace .mco-workspace --max-budget-usd 0.05` creates a smoke-test task and runs a fixed sentinel prompt through the real Claude Code adapter. It writes a sandbox contract, dispatch, execution report, usage snapshot, dashboard, and adapter smoke result. This command is opt-in and may consume provider budget.

`mco usage snapshot <task_id>` writes `USAGE_SNAPSHOT.json` under the task directory and registers it in the run ledger. The snapshot aggregates only task-local dispatch records and registered execution reports.
