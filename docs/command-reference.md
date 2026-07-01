# Command Reference

Command surface:

| Command | Purpose |
| --- | --- |
| `mco init` | Initialize a local workspace |
| `mco doctor` | Validate workspace readiness |
| `mco status` | Print compact workspace, latest task, dispatch, adapter gate, optional audit status, and explicit adapter doctor probes |
| `mco task create` | Create a task with `task.json`, `LOOP_SPEC.json`, and `RUN_LEDGER.json` |
| `mco task create --json` | Create a task and print machine-readable paths |
| `mco task list` | List workspace tasks |
| `mco task status` | Show task metadata |
| `mco task event` | Append an event to `RUN_LEDGER.json` |
| `mco artifact register` | Register evidence in the run ledger |
| `mco adapter capabilities` | Show adapter capability manifest for `generic-cli`, `claude-code`, or `kimi-code` |
| `mco adapter doctor` | Check adapter readiness against optional sandbox contract |
| `mco adapter matrix` | Show adapter readiness, quota, smoke, and promotion blockers |
| `mco adapter scaffold` | Create disabled adapter onboarding files |
| `mco adapter smoke` | Run an explicit opt-in real Claude Code or Kimi Code adapter smoke test |
| `mco dispatch queue` | Queue a dispatch for an agent |
| `mco dispatch list` | List task dispatches |
| `mco dispatch claim` | Claim a queued dispatch |
| `mco dispatch complete` | Complete a dispatch |
| `mco dispatch execute` | Validate adapter/sandbox gates, dry-run, run a safe command, or run a bounded Claude Code/Kimi Code prompt |
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

`mco status` is the fastest operator readout. By default it uses the adapter policy baseline and does not probe external CLI binaries or auth state. Add `--doctor` when you explicitly want local adapter checks:

```bash
mco status --workspace .mco-workspace
mco status --workspace .mco-workspace --doctor
mco status --workspace .mco-workspace --doctor --json
```

`mco dispatch queue <task_id> --agent kimi-code --title "Work" --instructions "..." --require-ready` is the queueing mode intended for auto-dispatch. It probes the adapter matrix and only writes an inbox file when readiness is `READY_SUPERVISED`. If the adapter is disabled, unknown, manual-only, or blocked, the dispatch is written as `status=blocked` with gate evidence and no inbox file.

`mco dispatch execute --command-json '["echo","hello"]'` runs a narrowly allowed command after sandbox enforcement. It is not an arbitrary shell runner.

`mco dispatch execute --agent claude-code --prompt-file <task-dir>/prompt.md --max-budget-usd 0.25` runs a supervised Claude Code prompt through `claude --print` with tools disabled, session persistence disabled, timeout/output limits, and a transcript artifact.

`mco dispatch execute --agent kimi-code --prompt-file <task-dir>/prompt.md` runs a supervised Kimi Code prompt through `kimi --prompt` with timeout/output limits and a transcript artifact. Kimi quota remains `unknown` unless future CLI evidence supports a narrower claim.

`mco adapter smoke claude-code --workspace .mco-workspace --max-budget-usd 0.05` creates a smoke-test task and runs a fixed sentinel prompt through the real Claude Code adapter. It writes a sandbox contract, dispatch, execution report, usage snapshot, dashboard, and adapter smoke result. This command is opt-in and may consume provider budget.

`mco adapter smoke kimi-code --workspace .mco-workspace` creates the same smoke-test evidence bundle through the real Kimi Code adapter. This command is opt-in and may consume provider budget; it has timeout/output caps but no per-run provider budget flag.

`mco adapter matrix --doctor --output adapter-matrix.json --html adapter-matrix.html` writes a machine-readable adapter comparison plus static HTML. Without `--doctor`, the command does not probe local CLI binaries. With `--doctor`, implemented adapters are probed and disabled template adapters remain non-executable.

`mco adapter scaffold kimi-code --output-dir adapter-kits/kimi-code` writes a disabled adapter manifest, sandbox contract draft, and smoke checklist. Scaffolded adapters are not executable until their gates are implemented and reviewed.

`mco usage snapshot <task_id>` writes `USAGE_SNAPSHOT.json` under the task directory and registers it in the run ledger. The snapshot aggregates only task-local dispatch records and registered execution reports.
