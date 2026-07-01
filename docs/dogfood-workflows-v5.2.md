# Dogfood Workflows v5.2

v5.2 adds three realistic workflow templates so the project is no longer demonstrated only through `hello-multi-cli`.

## Templates

| Template | Scenario | Close condition |
| --- | --- | --- |
| `documentation-release-loop` | Documentation, release notes, public launch materials | draft, verification report, verification ledger event, dashboard, close report |
| `frontend-review-loop` | Frontend implementation or UI review | implementation report, screenshot index, visual verification, dashboard, close report |
| `adapter-onboarding-loop` | New CLI adapter review | validation report, smoke review, verification event, dashboard, close report |

## Verification Run

The three templates were run locally with placeholder evidence in a temporary workspace. Each workflow reached:

```text
recommended_action=complete
reason=workflow completed
```

Observed output:

```text
documentation-release-loop complete workflow completed
frontend-review-loop complete workflow completed
adapter-onboarding-loop complete workflow completed
```

## What This Proves

- The templates are loadable by `mco orchestrate-start`.
- Their gates can advance through bounded `mco workflow loop` calls.
- They can produce a dashboard and replay artifact.
- They do not require provider CLI execution authority.
- They create a better dogfood base for future real tasks.

## What This Does Not Prove

- It does not prove provider-specific Claude/Kimi/Mimo/CodeWhale execution.
- It does not prove production merge conflict handling.
- It does not add automatic execution authority.

Those remain separate adapter-readiness and safety-gate concerns.

