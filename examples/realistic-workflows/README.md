# Realistic Workflow Examples

These examples are the v5.2 dogfood track. They are still bounded, local-first, and evidence-gated. They do not increase adapter execution authority.

## Included Templates

| Template | Scenario | Main evidence |
| --- | --- | --- |
| `documentation-release-loop` | Release notes, launch articles, docs updates | draft material, verification report, close report |
| `frontend-review-loop` | Mobile/page implementation review | implementation report, screenshot index, visual verification report |
| `adapter-onboarding-loop` | New CLI adapter review | validation report, smoke review, close report |

## Run One Template

```bash
mco init --workspace /tmp/mco-dogfood

mco orchestrate-start "Docs launch dogfood" \
  --template documentation-release-loop \
  --workspace /tmp/mco-dogfood
```

Then inspect:

```bash
mco workflow observe <task_id> --workspace /tmp/mco-dogfood
mco dashboard <task_id> --workspace /tmp/mco-dogfood
```

## Close a Dogfood Task with Placeholder Evidence

For local validation, create and register placeholder evidence inside the task directory, then run bounded workflow loops. Real projects should replace these placeholders with actual reports, screenshots, or adapter test output.

```bash
TASK_ID="<task_id>"
TASK_DIR="/tmp/mco-dogfood/tasks/$TASK_ID"

mkdir -p "$TASK_DIR/artifacts"
printf '# Draft\n\nDogfood draft.\n' > "$TASK_DIR/artifacts/draft-release-material.md"
mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/draft-release-material.md" \
  --label draft-release-material.md \
  --workspace /tmp/mco-dogfood

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-dogfood

printf '# Verification\n\nDogfood verification.\n' > "$TASK_DIR/artifacts/verification-report.md"
mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/verification-report.md" \
  --label verification-report.md \
  --workspace /tmp/mco-dogfood
mco task event "$TASK_ID" \
  --type verification \
  --message "Dogfood verification recorded." \
  --workspace /tmp/mco-dogfood
mco dashboard "$TASK_ID" --workspace /tmp/mco-dogfood

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-dogfood

printf '# Close\n\nDogfood close.\n' > "$TASK_DIR/artifacts/close-report.md"
mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/close-report.md" \
  --label close-report.md \
  --workspace /tmp/mco-dogfood

mco workflow loop "$TASK_ID" --max-steps 2 --workspace /tmp/mco-dogfood
mco workflow observe "$TASK_ID" --workspace /tmp/mco-dogfood
mco run replay "$TASK_DIR/RUN_LEDGER.json" --html "$TASK_DIR/replay.html"
```

## Safety Note

These workflows are examples of evidence gates, not a promise that provider CLIs should run automatically. Keep using `--require-ready`, adapter doctor checks, and smoke evidence before auto-dispatching real CLIs.
