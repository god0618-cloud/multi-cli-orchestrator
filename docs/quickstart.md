# Quickstart

This baseline proves the project can initialize a clean local workspace, create an evidence-backed task, run a sanitized hello workflow, validate adapter/sandbox gates, run a narrowly allowed safe command, run one supervised Claude Code prompt when Claude Code is installed and authenticated, replay a run ledger, and render a local dashboard without relying on private machine paths.

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

Run one supervised Claude Code prompt:

```bash
TASK_ID="$(
  mco task create "Claude adapter smoke" --json --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["task_id"])'
)"
TASK_DIR=".mco-workspace/tasks/$TASK_ID"
cp templates/sandbox-contracts/claude-code-supervised.json "$TASK_DIR/SANDBOX_CONTRACT.json"
printf 'Return exactly: MCO_ADAPTER_SMOKE_OK\n' > "$TASK_DIR/prompt.md"
DISPATCH_ID="$(
  mco dispatch queue "$TASK_ID" --agent claude-code --title "Claude smoke" --instructions "Return a fixed smoke string." --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["dispatch_id"])'
)"
mco adapter doctor claude-code --sandbox "$TASK_DIR/SANDBOX_CONTRACT.json"
mco dispatch execute "$TASK_ID" "$DISPATCH_ID" \
  --agent claude-code \
  --sandbox "$TASK_DIR/SANDBOX_CONTRACT.json" \
  --prompt-file "$TASK_DIR/prompt.md" \
  --timeout-seconds 120 \
  --max-budget-usd 0.25 \
  --workspace .mco-workspace
```

This path uses the host machine's Claude Code authentication. It sends the prompt to Claude, disables tools, disables session persistence, and writes a task-local execution report.

Run one supervised Kimi Code prompt:

```bash
TASK_ID="$(
  mco task create "Kimi adapter smoke" --json --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["task_id"])'
)"
TASK_DIR=".mco-workspace/tasks/$TASK_ID"
cp templates/sandbox-contracts/kimi-code-supervised.json "$TASK_DIR/SANDBOX_CONTRACT.json"
printf 'Return exactly: MCO_ADAPTER_SMOKE_OK\n' > "$TASK_DIR/prompt.md"
DISPATCH_ID="$(
  mco dispatch queue "$TASK_ID" --agent kimi-code --title "Kimi smoke" --instructions "Return a fixed smoke string." --workspace .mco-workspace \
    | python -c 'import json,sys; print(json.load(sys.stdin)["dispatch_id"])'
)"
mco adapter doctor kimi-code --sandbox "$TASK_DIR/SANDBOX_CONTRACT.json"
mco dispatch execute "$TASK_ID" "$DISPATCH_ID" \
  --agent kimi-code \
  --sandbox "$TASK_DIR/SANDBOX_CONTRACT.json" \
  --prompt-file "$TASK_DIR/prompt.md" \
  --timeout-seconds 120 \
  --workspace .mco-workspace
```

This path uses the host machine's Kimi Code authentication and writes a task-local execution report. Kimi quota remains `unknown` because the current command contract does not expose a per-run budget cap.
