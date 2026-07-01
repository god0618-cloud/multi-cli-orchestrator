# Tutorial: Adapter Onboarding Loop

Use this tutorial when you want to add or evaluate a new CLI adapter without pretending it is production-ready.

The adapter path is fake-fixture-first, disabled by default, and promotion-gated.

## When To Use This

- Evaluating a CLI such as Mimo Code, CodeWhale, or another coding assistant.
- Creating a public adapter contribution.
- Proving adapter contract shape before touching real credentials or provider quotas.

## Workflow Shape

| Phase | Owner | Evidence |
| --- | --- | --- |
| Scaffold | adapter contributor | generated adapter kit |
| Validate | contributor or verifier | `adapter-validation-report.md` |
| Smoke Review | verifier | `adapter-smoke-review.md` and a `verification` ledger event |
| Package | owner | dashboard HTML |
| Close | owner | `adapter-close-report.md` |

## Scaffold An Adapter Kit

```bash
mco adapter scaffold sample-cli --output-dir /tmp/mco-adapters/sample-cli
cd /tmp/mco-adapters/sample-cli
python test_sample_cli_adapter_contract.py
mco adapter validate-kit .
```

## Start The Workflow

```bash
mco init --workspace /tmp/mco-adapter-loop

mco orchestrate-start "Onboard sample CLI adapter" \
  --template adapter-onboarding-loop \
  --workspace /tmp/mco-adapter-loop
```

Set task variables:

```bash
TASK_ID="<task_id>"
TASK_DIR="/tmp/mco-adapter-loop/tasks/$TASK_ID"
mkdir -p "$TASK_DIR/artifacts"
```

Advance the initial scaffold phase. This phase is gated only by `LOOP_SPEC.json`, which `orchestrate-start` creates.

```bash
mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-adapter-loop
```

## Register Validation Evidence

```bash
printf '# Adapter Validation\n\nAdapter kit generated, fixture contract tests passed, and adapter remains disabled by default.\n' \
  > "$TASK_DIR/artifacts/adapter-validation-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/adapter-validation-report.md" \
  --label adapter-validation-report.md \
  --workspace /tmp/mco-adapter-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-adapter-loop
```

## Register Smoke Review Evidence

```bash
printf '# Adapter Smoke Review\n\nPASS for fixture-only readiness. Real provider execution is not enabled.\n' \
  > "$TASK_DIR/artifacts/adapter-smoke-review.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/adapter-smoke-review.md" \
  --label adapter-smoke-review.md \
  --workspace /tmp/mco-adapter-loop

mco task event "$TASK_ID" \
  --type verification \
  --message "Adapter smoke review recorded." \
  --workspace /tmp/mco-adapter-loop

mco dashboard "$TASK_ID" --workspace /tmp/mco-adapter-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-adapter-loop
```

## Package And Close

```bash
printf '# Close\n\nAdapter onboarding loop closed at fixture readiness.\n' \
  > "$TASK_DIR/artifacts/close-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/close-report.md" \
  --label close-report.md \
  --workspace /tmp/mco-adapter-loop

mco workflow loop "$TASK_ID" --max-steps 2 --workspace /tmp/mco-adapter-loop
mco workflow observe "$TASK_ID" --workspace /tmp/mco-adapter-loop
```

## Acceptance Criteria

- Adapter starts disabled by default.
- Fixture contract tests pass.
- A smoke review explicitly states whether real provider execution is enabled.
- Workflow reaches `recommended_action=complete` only after validation, smoke review, dashboard, and close evidence exist.

## Promotion Boundary

Do not promote an adapter from fixture-only readiness to supervised execution until it has:

- deterministic claim/execute/complete behavior,
- bounded workspace permissions,
- budget or quota visibility where available,
- failure-mode evidence,
- and an explicit maintainer decision.
