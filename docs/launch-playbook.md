# Launch Playbook

This playbook is for the v3.0 public MVP launch.

## Positioning

Multi-CLI Orchestrator is a local-first control plane for coordinating multiple AI coding CLIs as supervised workstations. It is not a replacement for Codex, Claude Code, Kimi Code, or other coding CLIs. It gives them a shared task bus, workflow gates, evidence artifacts, replayable run history, and a boss dashboard.

## Ideal First Users

- Developers who already use more than one AI coding CLI.
- Teams that want auditable handoffs instead of long prompt chains.
- Operators who need to see which CLI is ready, blocked, or waiting for a decision.
- Contributors who want to add a new CLI adapter safely.

## Demo Script

```bash
git clone https://github.com/god0618-cloud/multi-cli-orchestrator.git
cd multi-cli-orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .
mco init --workspace .mco-workspace
mco doctor --workspace .mco-workspace
mco demo hello-multi-cli --workspace .mco-demo
TASK_ID="$(find .mco-demo/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | head -1)"
mco run replay ".mco-demo/tasks/$TASK_ID/RUN_LEDGER.json"
mco dashboard "$TASK_ID" --workspace .mco-demo
```

Expected outcome:

- A task directory is created.
- `LOOP_SPEC.json`, `RUN_LEDGER.json`, `plan.json`, and evidence artifacts exist.
- Replay prints the run ledger.
- Dashboard HTML renders without external services.

## Adapter Contributor Demo

```bash
mco adapter scaffold my-cli --output-dir adapter-kits/my-cli
cd adapter-kits/my-cli
python test_my_cli_adapter_contract.py
```

This proves that new adapters start fake-fixture-first and disabled by default.

## Release Gate

Before publishing a tag or release:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q src tests
python -m mco.cli release check . --json
python -m mco.cli audit .
```

Then perform a public clone smoke in a fresh directory using Python 3.10+.

## Messaging

Lead with:

- "CLIs are workstations."
- "Loops beat prompts."
- "Evidence before claims."
- "Sandboxes before parallelism."

Avoid claiming:

- autonomous production deployment
- arbitrary shell execution
- provider-account quota visibility
- adapter readiness without doctor/smoke evidence

## Recommended GitHub Topics

`ai-agents`, `cli`, `orchestration`, `multi-agent`, `local-first`, `codex`, `claude-code`, `kimi-code`, `developer-tools`, `automation`
