# Command Reference

v1.0 command surface:

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
| `mco adapter capabilities` | Show generic adapter capability manifest |
| `mco adapter doctor` | Check adapter readiness against optional sandbox contract |
| `mco dispatch queue` | Queue a dispatch for an agent |
| `mco dispatch list` | List task dispatches |
| `mco dispatch claim` | Claim a queued dispatch |
| `mco dispatch complete` | Complete a dispatch |
| `mco dispatch execute` | Validate adapter/sandbox gates, dry-run, or run a safe command |
| `mco dashboard` | Render a static task dashboard |
| `mco orchestrate-start` | Create a task and initialize a workflow plan |
| `mco schema validate` | Validate loop spec, adapter manifest, sandbox contract, or run ledger |
| `mco serve` | Serve a workspace directory over HTTP |
| `mco audit` | Run minimal safety audit |
| `mco demo hello-multi-cli` | Run sanitized built-in demo |
| `mco run replay` | Print a read-only timeline from `RUN_LEDGER.json` |
| `mco release check` | Run release readiness checks |

`mco dispatch execute --dry-run` validates gates and writes evidence only.

`mco dispatch execute --command-json '["echo","hello"]'` runs a narrowly allowed command after sandbox enforcement. It is not an arbitrary shell runner and does not execute real external CLI workers yet.
