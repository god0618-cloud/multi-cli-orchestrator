# Dogfood Workflows

MCO includes realistic workflow templates so the project is no longer demonstrated only through `hello-multi-cli`.

## Templates

| Template | Scenario | Close condition |
| --- | --- | --- |
| `documentation-release-loop` | Documentation, release notes, public launch materials | draft, verification report, verification ledger event, dashboard, close report |
| `frontend-review-loop` | Frontend implementation or UI review | prototype brief, plan review, implementation report, browser/visual evidence, visual verification, dashboard, close report |
| `prototype-brief-loop` | Spec-first product/UI prototype | prototype brief, plan review, prototype implementation report, browser/visual evidence, visual verification, close report |
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
prototype-brief-loop complete workflow completed
adapter-onboarding-loop complete workflow completed
```

## What This Proves

- The templates are loadable by `mco orchestrate-start`.
- Their gates can advance through bounded `mco workflow loop` calls.
- They can produce a dashboard and replay artifact.
- They do not require provider CLI execution authority.
- Public templates default to a single-agent path unless they explicitly declare otherwise.
- They create a better dogfood base for future real tasks.

## What This Does Not Prove

- It does not prove provider-specific Claude/Kimi/Mimo/CodeWhale execution.
- It does not prove production merge conflict handling.
- It does not add automatic execution authority.

Those remain separate adapter-readiness and safety-gate concerns.
