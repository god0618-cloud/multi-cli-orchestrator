# Hello Multi-CLI

This sanitized demo proves the lifecycle without requiring any private CLI, credential, or local knowledge base.

Fast path:

```bash
mco demo hello-multi-cli --workspace .demo-workspace
TASK_ID="$(find .demo-workspace/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \\; | head -1)"
mco run replay ".demo-workspace/tasks/$TASK_ID/RUN_LEDGER.json"
open ".demo-workspace/tasks/$TASK_ID/dashboard.html"
```

Safe execution example:

```bash
cp templates/sandbox-contracts/single-worker.json ".demo-workspace/tasks/$TASK_ID/SANDBOX_CONTRACT.json"
DISPATCH_ID="$(
  mco dispatch queue "$TASK_ID" --agent generic-cli --title "Echo evidence" --instructions "Produce evidence." --workspace .demo-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["dispatch_id"])'
)"
mco dispatch execute "$TASK_ID" "$DISPATCH_ID" \
  --agent generic-cli \
  --sandbox ".demo-workspace/tasks/$TASK_ID/SANDBOX_CONTRACT.json" \
  --command-json '["echo","hello-from-demo"]' \
  --workspace .demo-workspace
```

Expected files:

```text
.demo-workspace/tasks/<task_id>/task.json
.demo-workspace/tasks/<task_id>/LOOP_SPEC.json
.demo-workspace/tasks/<task_id>/RUN_LEDGER.json
.demo-workspace/tasks/<task_id>/plan.json
.demo-workspace/tasks/<task_id>/artifacts/demo-evidence.md
.demo-workspace/tasks/<task_id>/dashboard.html
```

Manual path:

```bash
mco init --workspace .demo-workspace
mco orchestrate-start "Hello Multi-CLI" --template hello-multi-cli --workspace .demo-workspace
TASK_ID="$(find .demo-workspace/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \\; | head -1)"
mco task event "$TASK_ID" --type verification --message "Demo verification event." --workspace .demo-workspace
echo "# Demo Evidence" > .demo-workspace/evidence.md
mco artifact register "$TASK_ID" .demo-workspace/evidence.md --label demo-evidence --workspace .demo-workspace
mco dashboard "$TASK_ID" --workspace .demo-workspace
```

Open:

```text
.demo-workspace/tasks/<task_id>/dashboard.html
```
