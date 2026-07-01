# Tutorial: Documentation Release Loop

Use this tutorial when you want one CLI to draft public-facing material and another lane to verify that the output is safe to publish.

The workflow is intentionally conservative. It proves evidence-gated coordination, not unsupervised publishing.

## When To Use This

- Release notes, README updates, launch posts, public docs, or internal rollout notes.
- Work where wording drift, private-path leakage, or unsupported claims are the main risks.
- Tasks that need a clear close report before a human publishes anything externally.

## Workflow Shape

| Phase | Owner | Evidence |
| --- | --- | --- |
| Draft | writer or docs CLI | `draft-release-material.md` |
| Verify | reviewer or verifier CLI | `verification-report.md` and a `verification` ledger event |
| Package | owner | dashboard HTML |
| Close | owner | `close-report.md` |

## Run It Locally

```bash
mco init --workspace /tmp/mco-docs-loop

mco orchestrate-start "Prepare public release material" \
  --template documentation-release-loop \
  --workspace /tmp/mco-docs-loop
```

Find the generated task id:

```bash
find /tmp/mco-docs-loop/tasks -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
```

Set it for the rest of the tutorial:

```bash
TASK_ID="<task_id>"
TASK_DIR="/tmp/mco-docs-loop/tasks/$TASK_ID"
mkdir -p "$TASK_DIR/artifacts"
```

Advance the initial brief phase. This phase is gated only by `LOOP_SPEC.json`, which `orchestrate-start` creates.

```bash
mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-docs-loop
```

## Register Draft Evidence

```bash
printf '# Draft\n\nPublic release material draft.\n' > "$TASK_DIR/artifacts/draft-release-material.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/draft-release-material.md" \
  --label draft-release-material.md \
  --workspace /tmp/mco-docs-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-docs-loop
```

## Register Verification Evidence

```bash
printf '# Verification\n\nNo private paths, unsupported claims, or missing release gates found.\n' \
  > "$TASK_DIR/artifacts/verification-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/verification-report.md" \
  --label verification-report.md \
  --workspace /tmp/mco-docs-loop

mco task event "$TASK_ID" \
  --type verification \
  --message "Release material verification recorded." \
  --workspace /tmp/mco-docs-loop

mco dashboard "$TASK_ID" --workspace /tmp/mco-docs-loop
mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-docs-loop
```

## Close The Loop

```bash
printf '# Close\n\nDocumentation release loop closed with evidence.\n' \
  > "$TASK_DIR/artifacts/close-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/close-report.md" \
  --label close-report.md \
  --workspace /tmp/mco-docs-loop

mco workflow loop "$TASK_ID" --max-steps 2 --workspace /tmp/mco-docs-loop
mco workflow observe "$TASK_ID" --workspace /tmp/mco-docs-loop
mco run replay "$TASK_DIR/RUN_LEDGER.json" --html "$TASK_DIR/replay.html"
```

## Acceptance Criteria

- `mco workflow observe` reports `recommended_action=complete`.
- `RUN_LEDGER.json` contains draft, verification, dashboard, and close events.
- Dashboard HTML exists and can be opened locally.
- No external publish action happened automatically.

## Common Failure Modes

- Missing verification ledger event: register the report and also run `mco task event --type verification`.
- Draft exists but phase does not advance: confirm the artifact label matches the workflow gate.
- Release material contains local/private paths: fix the draft and record a new verification report before close.
