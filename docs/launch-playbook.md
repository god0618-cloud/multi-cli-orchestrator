# Launch Playbook

This playbook is for the v5 public Alpha launch track.

## Positioning

Multi-CLI Orchestrator is a local-first control plane for coordinating multiple AI coding CLIs as supervised workstations.

It is not a replacement for Codex, Claude Code, Kimi Code, Mimo Code, CodeWhale, or other coding CLIs. It gives them a shared task workspace, workflow gates, evidence artifacts, replayable run history, adapter readiness visibility, and a boss dashboard.

## Ideal First Users

- Developers who already use more than one AI coding CLI.
- Teams that want auditable handoffs instead of long prompt chains.
- Operators who need to see which CLI is ready, blocked, or waiting for a decision.
- Contributors who want to add a new CLI adapter safely.
- People experimenting with Agent OS patterns who care about evidence and safety boundaries.

## Demo Script

```bash
git clone https://github.com/god0618-cloud/multi-cli-orchestrator.git
cd multi-cli-orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .

mco demo walkthrough \
  --workspace /tmp/mco-public-demo \
  --output-dir /tmp/mco-public-demo-output

open /tmp/mco-public-demo-output/RUN_REPLAY.html
```

Expected outcome:

- A task directory is created in `/tmp`.
- `LOOP_SPEC.json`, `RUN_LEDGER.json`, `plan.json`, and evidence artifacts exist.
- Replay HTML renders without external services.
- The walkthrough also generates a disabled adapter kit.

## Visual Assets

- Dashboard screenshot: `docs/assets/demo-dashboard-v5.9-en.png`
- Dashboard Chinese screenshot: `docs/assets/demo-dashboard-v5.9-zh.png`
- Run replay screenshot: `docs/assets/demo-run-replay-v5.1.png`
- Adapter matrix screenshot: `docs/assets/demo-adapter-matrix-v5.1.png`
- Demo story: `docs/demo-story-v5.1.md`

## Adapter Contributor Demo

```bash
mco adapter scaffold my-cli --output-dir /tmp/adapter-kits/my-cli
cd /tmp/adapter-kits/my-cli
python test_my_cli_adapter_contract.py
mco adapter validate-kit .
```

This proves that new adapters start fake-fixture-first and disabled by default.

## Release Gate

Before publishing a tag or release:

```bash
PYTHONPATH=src python3 -m unittest tests.unit.test_workspace
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mco.cli release check . --json
PYTHONPATH=src python3 -m mco.cli audit .
```

Then perform a public clone smoke in a fresh directory using Python 3.10+.

## Messaging

Lead with:

- "CLIs are workstations."
- "Loops beat prompts."
- "Evidence before claims."
- "Sandboxes before parallelism."
- "Automation earns authority through gates."

Avoid claiming:

- autonomous production deployment
- arbitrary shell execution
- provider-account quota visibility
- adapter readiness without doctor/smoke evidence
- real concurrent provider execution
- organization-wide permission management

## Recommended GitHub Topics

`ai-agents`, `ai-coding`, `agent-os`, `cli`, `orchestration`, `multi-agent`, `local-first`, `codex`, `claude-code`, `kimi-code`, `developer-tools`, `workflow-automation`, `automation`
