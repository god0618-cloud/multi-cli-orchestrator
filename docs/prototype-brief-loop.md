# Prototype Brief Loop

`prototype-brief-loop` is the spec-first workflow for turning an idea into a reviewable prototype without letting the work drift into an unbounded demo.

It was added after dogfooding showed a repeated failure mode: a CLI can implement a plausible interface before the page goal, role model, state matrix, and acceptance evidence are explicit. The result looks active but is hard to judge. This loop moves the quality decision before worker fanout.

The default posture is still `stack: single` and `evidence_level: L1`. One agent should be able to run the loop locally; multi-CLI fanout is an optimization after plan review, not a requirement.

## Workflow Shape

| Phase | Gate | Required Evidence |
| --- | --- | --- |
| `brief` | `loop_spec_exists` | `prototype-brief.md` |
| `plan_review` | `prototype_brief_exists`, `plan_review_passed` | `plan-review-report.md` + `plan_review_passed` event |
| `prototype` | implementation + browser evidence + clean dispatches | `prototype-implementation-report.md`, `browser-visual-evidence.json` |
| `visual_verify` | verification event + dashboard | `visual-verification-report.md`, `dashboard.html` |
| `close` | close artifact + clean dispatches | `close-report.md` |

## Prototype Brief Minimum

`prototype-brief.md` should include:

- Page or flow goal.
- Target role and primary job-to-be-done.
- Information architecture.
- Business flow and state transitions.
- State matrix: loading, empty, error, success, disabled, permission-limited.
- Field constraints and validation rules.
- Primary and secondary interactions.
- Visual/design-system constraints.
- Acceptance criteria.
- Non-goals.
- Evidence plan: route, viewport, actions, screenshots, and verification owner.

## Browser Visual Evidence

`browser-visual-evidence.json` is the compact proof that the prototype was exercised in a browser-like surface. At L1, this can be as small as one final-state screenshot plus the route and viewport. It should include:

```json
{
  "schema": "mco.browser_visual_evidence.v1.0",
  "viewport": "390x844",
  "actions": ["open route", "tap primary action", "capture resulting state"],
  "screenshots": ["home.png", "detail.png"],
  "result": "PASS",
  "notes": "No text overflow; empty state and disabled action checked."
}
```

This file is intentionally separate from screenshots. Screenshots show what it looked like; the evidence manifest says what was actually exercised.

## Local Run

```bash
mco init --workspace /tmp/mco-prototype-loop

mco orchestrate-start "Prototype checkout flow" \
  --template prototype-brief-loop \
  --workspace /tmp/mco-prototype-loop

TASK_ID="<task_id>"
mco workflow observe "$TASK_ID" --workspace /tmp/mco-prototype-loop
```

Use `mco workflow loop "$TASK_ID" --max-steps 1` only after the current phase evidence is registered.

## Stop Rules

Stop instead of continuing when:

- The brief is missing a business flow or state matrix.
- Plan review has not produced a clear PASS.
- Browser evidence does not name viewport, route, actions, and screenshots.
- Any dispatch is failed or blocked.
- A user decision gate is reached.
