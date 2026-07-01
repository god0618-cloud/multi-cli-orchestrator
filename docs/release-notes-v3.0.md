# Multi-CLI Orchestrator v3.0.0

v3.0.0 is the first public open-source MVP baseline for Multi-CLI Orchestrator.

## What It Is

Multi-CLI Orchestrator is a local-first control plane for coordinating multiple AI coding CLIs as supervised workstations. It gives existing CLIs a shared task workspace, workflow gates, evidence artifacts, replayable run history, adapter readiness checks, and a static boss dashboard.

## Highlights

- Runnable `hello-multi-cli` demo.
- Task-local `LOOP_SPEC.json`, `RUN_LEDGER.json`, `plan.json`, dispatch inboxes, and artifact evidence.
- Static boss dashboard with adapter matrix, dispatch gate posture, usage snapshot, artifacts, and timeline.
- Safe command execution path for narrowly allowlisted commands.
- Supervised Claude Code and Kimi Code prompt adapters.
- Explicit adapter doctor, smoke, matrix, and status commands.
- Bounded monitor snapshots.
- Phase-gated workflow status and advancement.
- Disabled-by-default adapter contributor kits with README, fake CLI fixture, and unittest contract template.

## Safety Model

- No arbitrary shell execution.
- New adapters start disabled.
- Real provider adapter smoke tests are opt-in.
- Provider quota is reported only when there is task-local evidence.
- Workflow advancement is fail-stop when gates fail.

## Quick Smoke

```bash
git clone https://github.com/god0618-cloud/multi-cli-orchestrator.git
cd multi-cli-orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .
mco demo hello-multi-cli --workspace .mco-demo
TASK_ID="$(find .mco-demo/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | head -1)"
mco run replay ".mco-demo/tasks/$TASK_ID/RUN_LEDGER.json"
python -m mco.cli release check . --json
python -m mco.cli audit .
```

## Known Limits

- Multi-worker execution is still intentionally conservative.
- Replay UI is not implemented yet.
- Mimo and CodeWhale adapters remain disabled templates until their command contracts are proven.
- Real provider quota visibility depends on each provider CLI exposing reliable evidence.
