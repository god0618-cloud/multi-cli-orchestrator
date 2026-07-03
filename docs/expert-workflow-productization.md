# Expert Workflow Productization

This note records the product direction behind the workflow-template upgrade: reusable AI-agent workflows should encode expert operating judgment, not just longer prompts.

## What Was Absorbed

Recent community practice around agent skills and browser automation points to the same pattern:

- Skills are most useful when they package workflow, quality gates, and decision boundaries.
- Implementation should wait until the product brief and plan review are explicit.
- Browser automation should produce structured evidence, not only screenshots.
- Autonomous loops need stop conditions, escalation rules, and bounded worker fanout.
- Token/context budget is a workflow resource, not an afterthought.
- Single-agent closure is the default user path; multi-CLI fanout is an enhancement.

MCO absorbs these lessons as local-first primitives:

| Practice | MCO Primitive |
| --- | --- |
| Skill as reusable workflow | Workflow template manifest |
| Plan before fanout | `plan_review_passed` gate |
| Product prototype brief | `prototype-brief.md` + `prototype_brief_exists` gate |
| Browser execution evidence | `browser-visual-evidence.json` + `browser_visual_evidence_registered` gate |
| Skill promotion discipline | L1/L2 rubric in `docs/skill-evaluation-rubric.md` |
| Community note absorption | Four-section note template in `docs/note-absorption-template.md` |

## Why This Matters

Without these gates, multi-CLI orchestration can look busy while still producing demo-grade work. A worker can start too soon, implement a plausible screen, and leave the human to judge quality visually after the fact.

The upgraded loop changes the default order:

1. Clarify the product surface.
2. Review the plan.
3. Prefer a single-agent path when it is enough.
4. Only then fan out implementation.
5. Verify through browser/visual evidence.
6. Close only with durable artifacts.

## Implemented Assets

- `prototype-brief-loop` workflow template.
- Optional workflow-template `manifest` validation and persistence into `plan.json`.
- Semantic gates:
  - `prototype_brief_exists`
  - `plan_review_passed`
  - `browser_visual_evidence_registered`
  - `skill_evaluation_rubric_exists`
- Frontend review loop upgraded to require prototype brief and plan review before implementation.
- Browser/visual evidence manifest replaces loose screenshot index as the implementation gate.
- Workflow manifests can declare `stack`, `evidence_level`, and `budget`.
- Skill evaluation now has a lightweight L1 gate and a deeper L2 promotion review.
- Community notes use a four-section absorption template: what it says, reality check, signal, decision.

## Verification

The implementation is covered by unit tests that prove:

- `prototype-brief-loop` initializes from a clean workspace.
- Plan review cannot pass with artifacts alone; it also needs a `plan_review_passed` ledger event.
- Prototype implementation cannot advance without `browser-visual-evidence.json`.
- Workflow manifests are copied into `plan.json`.
- Packaged templates and source templates stay in sync.
