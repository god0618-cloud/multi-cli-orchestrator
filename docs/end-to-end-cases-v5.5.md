# End-to-End Cases

The dogfood workflow templates are available as runnable user-facing tutorials.

The goal is simple: a new user should be able to understand what kind of work fits Multi-CLI Orchestrator, run a bounded local version, inspect evidence, and see the close condition without needing the original development history.

## Included Tutorials

| Tutorial | Best For | Template |
| --- | --- | --- |
| [Documentation release loop](tutorials/documentation-release-loop.md) | Release notes, public docs, launch posts | `documentation-release-loop` |
| [Frontend review loop](tutorials/frontend-review-loop.md) | UI implementation review with prototype brief, plan review, and browser/visual evidence | `frontend-review-loop` |
| [Prototype brief loop](prototype-brief-loop.md) | Spec-first product prototype work | `prototype-brief-loop` |
| [Adapter onboarding loop](tutorials/adapter-onboarding-loop.md) | Adding a new CLI adapter safely | `adapter-onboarding-loop` |

## Shared Pattern

Each tutorial follows the same loop:

1. Start a local workspace in `/tmp`.
2. Start a workflow from a named template.
3. Register concrete artifacts at each phase gate.
4. Advance with bounded `mco workflow loop --max-steps`.
5. Generate dashboard or replay evidence.
6. Close only after the final report exists.

## Why This Matters

Before the tutorial track, the repository could prove the machinery worked, but the path was still too close to maintainer knowledge. The current tutorial set makes the project easier to evaluate from the outside:

- operators can see what a good loop looks like,
- contributors can copy a known shape,
- safety reviewers can inspect what is intentionally not automated,
- and future examples have a standard tutorial format.

## Non-Goals

- No new adapter authority.
- No provider credential flow.
- No hosted service.
- No claim that placeholder evidence is enough for production work.

Real projects should replace tutorial placeholders with actual documents, screenshots, test logs, adapter smoke output, or reviewer reports.

## Acceptance

- All three tutorials name the workflow template they use.
- All three tutorials include phase evidence, close criteria, and common failure modes.
- The README links to the tutorial index.
- Release checks remain clean.
