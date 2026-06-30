# Quickstart

This v1.0 baseline proves the project can initialize a clean local workspace, create an evidence-backed task, run a sanitized hello workflow, validate adapter/sandbox gates, run a narrowly allowed safe command, replay a run ledger, and render a local dashboard without relying on private machine paths.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
mco init --workspace .mco-workspace
mco doctor --workspace .mco-workspace
mco task create "Hello multi-CLI" --workspace .mco-workspace
mco task list --workspace .mco-workspace
mco orchestrate-start "Hello orchestrated task" --template hello-multi-cli --workspace .mco-workspace
mco demo hello-multi-cli --workspace .mco-demo
DEMO_TASK_ID="$(find .mco-demo/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \\; | head -1)"
mco run replay ".mco-demo/tasks/$DEMO_TASK_ID/RUN_LEDGER.json"
```

Expected result:

```text
PASS config: mco.workspace.v0.2
PASS loop_spec_template: ...
```

Render a dashboard:

```bash
TASK_ID="$(find .mco-workspace/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \\; | head -1)"
mco dashboard "$TASK_ID" --workspace .mco-workspace
```

Run one supervised safe command:

```bash
TASK_ID="$(
  mco task create "Safe command smoke" --json --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["task_id"])'
)"
TASK_DIR=".mco-workspace/tasks/$TASK_ID"
cp templates/sandbox-contracts/single-worker.json "$TASK_DIR/SANDBOX_CONTRACT.json"
DISPATCH_ID="$(
  mco dispatch queue "$TASK_ID" --agent generic-cli --title "Echo evidence" --instructions "Create command evidence." --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["dispatch_id"])'
)"
mco dispatch execute "$TASK_ID" "$DISPATCH_ID" \
  --agent generic-cli \
  --sandbox "$TASK_DIR/SANDBOX_CONTRACT.json" \
  --command-json '["echo","hello-from-mco"]' \
  --workspace .mco-workspace
mco run replay "$TASK_DIR/RUN_LEDGER.json"
```
