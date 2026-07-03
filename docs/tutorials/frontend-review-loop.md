# Tutorial: Frontend Review Loop

Use this tutorial when a frontend change needs visible evidence before it is accepted.

The loop does not judge aesthetics by vibes. It requires a prototype brief, a plan review, implementation notes, browser/visual evidence, and a visual verification report.

## When To Use This

- Mobile-first page implementation.
- UI refactor or visual polish.
- Design-system alignment checks.
- Screenshot-based review before merge.

## Workflow Shape

| Phase | Owner | Evidence |
| --- | --- | --- |
| Spec | designer | `prototype-brief.md` |
| Plan Review | reviewer | `plan-review-report.md` + `plan_review_passed` event |
| Implement | frontend CLI | `implementation-report.md` |
| Capture | frontend CLI or verifier | `browser-visual-evidence.json` |
| Verify | reviewer | `visual-verification-report.md` |
| Package | owner | dashboard HTML |
| Close | owner | `frontend-close-report.md` |

## Run It Locally

```bash
mco init --workspace /tmp/mco-frontend-loop

mco orchestrate-start "Review mobile project page" \
  --template frontend-review-loop \
  --workspace /tmp/mco-frontend-loop
```

Set task variables:

```bash
TASK_ID="<task_id>"
TASK_DIR="/tmp/mco-frontend-loop/tasks/$TASK_ID"
mkdir -p "$TASK_DIR/artifacts"
```

Advance the initial spec phase. This phase is gated only by `LOOP_SPEC.json`, which `orchestrate-start` creates.

```bash
mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-frontend-loop
```

## Register Prototype Brief And Plan Review

The implementation phase must not start until the prototype brief is registered and the plan review has explicitly passed.

```bash
printf '# Prototype Brief\n\nPage goal, roles, information architecture, state matrix, interactions, and acceptance criteria.\n' \
  > "$TASK_DIR/artifacts/prototype-brief.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/prototype-brief.md" \
  --label prototype-brief.md \
  --workspace /tmp/mco-frontend-loop

printf '# Plan Review\n\nPASS. Scope, acceptance criteria, and evidence plan are clear enough for implementation.\n' \
  > "$TASK_DIR/artifacts/plan-review-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/plan-review-report.md" \
  --label plan-review-report.md \
  --workspace /tmp/mco-frontend-loop

mco task event "$TASK_ID" \
  --type plan_review_passed \
  --message "Frontend plan review passed before worker fanout." \
  --workspace /tmp/mco-frontend-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-frontend-loop
```

## Register Implementation Evidence

```bash
printf '# Implementation\n\nImplemented the target page and ran the local build.\n' \
  > "$TASK_DIR/artifacts/implementation-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/implementation-report.md" \
  --label implementation-report.md \
  --workspace /tmp/mco-frontend-loop
```

Register the browser/visual evidence manifest required by the same implementation gate:

```bash
cat > "$TASK_DIR/artifacts/browser-visual-evidence.json" <<'JSON'
{
  "schema": "mco.browser_visual_evidence.v1.0",
  "viewport": "390x844",
  "actions": ["open target route", "exercise primary action", "capture terminal state"],
  "screenshots": ["mobile-home.png", "mobile-detail.png"],
  "result": "PASS"
}
JSON

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/browser-visual-evidence.json" \
  --label browser-visual-evidence.json \
  --workspace /tmp/mco-frontend-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-frontend-loop
```

## Register Visual Verification

```bash
printf '# Visual Verification\n\nPASS. Mobile layout, text wrapping, primary actions, and empty states were checked.\n' \
  > "$TASK_DIR/artifacts/visual-verification-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/visual-verification-report.md" \
  --label visual-verification-report.md \
  --workspace /tmp/mco-frontend-loop

mco task event "$TASK_ID" \
  --type verification \
  --message "Frontend visual verification recorded." \
  --workspace /tmp/mco-frontend-loop

mco dashboard "$TASK_ID" --workspace /tmp/mco-frontend-loop

mco workflow loop "$TASK_ID" --max-steps 1 --workspace /tmp/mco-frontend-loop
```

## Package And Close

```bash
printf '# Close\n\nFrontend review loop closed with screenshots and visual verification.\n' \
  > "$TASK_DIR/artifacts/close-report.md"

mco artifact register "$TASK_ID" \
  "$TASK_DIR/artifacts/close-report.md" \
  --label close-report.md \
  --workspace /tmp/mco-frontend-loop

mco workflow loop "$TASK_ID" --max-steps 2 --workspace /tmp/mco-frontend-loop
mco workflow observe "$TASK_ID" --workspace /tmp/mco-frontend-loop
```

## Acceptance Criteria

- `recommended_action=complete`.
- Prototype brief and plan review exist before implementation.
- Browser/visual evidence exists before visual verification.
- Visual verification is an artifact, not a chat claim.
- Dashboard reflects the current phase and artifacts.

## Common Failure Modes

- Implementation starts before plan review: register `prototype-brief.md`, `plan-review-report.md`, and a `plan_review_passed` event first.
- Screenshots are not registered as browser evidence: create `browser-visual-evidence.json` even if images live elsewhere.
- Visual verification is too vague: name the viewport, key screens, and checked criteria.
- The loop is used as a design substitute: this tutorial verifies a frontend pass; it does not replace PRD or design decisions.
