# Good First Issues

These are starter-sized contribution ideas that fit the current v5.x public Alpha stage.

## Documentation

| Idea | Why it helps | Acceptance |
| --- | --- | --- |
| Improve a quickstart step | Reduces first-run friction | Fresh clone commands still pass |
| Add a troubleshooting entry | Helps users recover without maintainer help | Includes exact command, symptom, and fix |
| Add a glossary entry | Makes the control-plane model easier to understand | Term appears in docs with one concrete example |

## Workflow Templates

| Idea | Why it helps | Acceptance |
| --- | --- | --- |
| Add a docs-review workflow variant | Common open-source task | Template loads and reaches a bounded wait/complete state |
| Add a code-review workflow variant | Useful without provider execution | Uses artifact and ledger gates, not vague prompt claims |
| Improve realistic workflow examples | Makes dogfooding clearer | Commands are copy-pasteable and do not expose private paths |

## Adapter Kits

| Idea | Why it helps | Acceptance |
| --- | --- | --- |
| Add a fake CLI fixture scenario | Strengthens adapter validation | `mco adapter validate-kit` passes |
| Improve adapter smoke checklist | Makes promotion safer | Checklist covers sandbox, quota, timeout, transcript, and failure behavior |
| Document a manual-only CLI | Keeps unsafe adapters visible without auto-dispatch | Adapter request includes command contract evidence |

## Dashboard / Replay

| Idea | Why it helps | Acceptance |
| --- | --- | --- |
| Improve dashboard copy | Helps owners understand why a loop stops | No layout regression; audit passes |
| Add replay explanation docs | Makes evidence easier to interpret | Includes one before/after example |
| Add screenshot guidance | Prevents private path leaks | Mentions temporary workspaces and redaction scan |

## Rules for Good First Issues

- No provider credentials.
- No real provider calls in CI.
- No broad execution authority.
- No private local paths.
- Must include verification commands.

