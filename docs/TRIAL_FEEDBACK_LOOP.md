# Trial Feedback Loop

This project should improve through real trial evidence, not vague impressions.

Use this loop when someone tries the quickstart, demo walkthrough, workflow tutorials, dashboard, replay, or adapter scaffold and reports friction.

## Feedback Intake

Preferred channel: GitHub issue template **Trial feedback**.

Required evidence:

- path tried,
- exact sanitized commands,
- result category,
- logs, screenshots, dashboard snippets, or `RUN_LEDGER.json` snippets,
- what would have made the trial easier.

Reports must not include credentials, private paths, business data, or native CLI memory/profile contents.

## Triage Categories

| Category | Meaning | Default action |
| --- | --- | --- |
| Setup blocker | Install, Python version, shell, or package issue | bug or docs fix |
| Command mismatch | Docs command does not match CLI behavior | bug, test, docs patch |
| Concept confusion | User cannot tell what MCO does or does not do | README/docs copy improvement |
| Workflow friction | Gates are correct but too hard to understand | tutorial/dashboard improvement |
| Adapter readiness | User wants a CLI promoted or connected | adapter request, maturity review |
| Safety concern | Privacy, quota, sandbox, or memory boundary issue | safety issue, stop promotion until resolved |

## Maintainer Loop

1. Reproduce the issue in `/tmp` using the reported commands.
2. Capture the smallest failing command or confusing screen.
3. Classify severity:
   - P0: safety boundary, credential/privacy leak, or unsafe execution.
   - P1: public quickstart/tutorial cannot complete.
   - P2: confusing docs or dashboard wording.
   - P3: enhancement or polish.
4. Decide the owner:
   - docs,
   - workflow template,
   - dashboard,
   - adapter kit,
   - core CLI.
5. Patch with evidence.
6. Run release checks.
7. Reply with the commit, verification, and remaining limitation.

## Close Criteria

A feedback issue can close when:

- the reported command path has been reproduced or clearly cannot be reproduced,
- a fix, docs clarification, or explicit non-goal was recorded,
- tests or release checks cover the change when applicable,
- safety boundaries were not loosened without a separate maintainer decision.

## Trial Backlog Labels

Recommended labels:

- `trial-feedback`
- `needs-repro`
- `docs`
- `dashboard`
- `workflow`
- `adapter`
- `safety`
- `good-first-issue`

## What Not To Do

- Do not convert trial feedback into automatic provider execution.
- Do not accept screenshots or logs with secrets.
- Do not promote adapters based on enthusiasm alone.
- Do not add broad features before the failed trial path is reproducible.
