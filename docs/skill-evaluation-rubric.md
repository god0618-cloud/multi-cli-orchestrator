# Skill Evaluation Rubric

MCO treats a reusable skill or workflow as a product surface, not a prompt snippet. The evaluation path is intentionally two-level: most skills should pass through a tiny L1 gate first, and only frequently used or risky skills need the heavier L2 review.

## L1: Admission Gate

Every new skill needs only three fields before it can be tried on a bounded task.

| Field | Required Answer |
| --- | --- |
| `trigger` | When should this skill be used? Include one clear non-trigger. |
| `stop_condition` | When should the skill stop or escalate instead of continuing? |
| `token_budget` | Expected average token cost, hard cap, and defer policy. |

Recommended shape:

```yaml
trigger: "Use when a frontend task needs visual review before acceptance; do not use for backend-only work."
stop_condition: "Stop if the target route, viewport, or acceptance criteria are missing."
token_budget:
  avg_token_cost: 3000
  hard_cap: 8000
  defer_policy: "Move screenshots and detailed findings into artifacts; keep the controller summary compact."
```

L1 is enough for:

- First dogfood runs.
- Low-risk one-agent tasks.
- Skills that mostly route or summarize.

## L2: Promotion Review

Escalate a skill to L2 when it is called repeatedly, causes one material failure, changes code or knowledge bases, or becomes part of a public workflow template.

Score each dimension from 0 to 2.

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Trigger Clarity | Trigger is vague | Trigger is named but broad | Trigger and non-trigger are explicit |
| Required Inputs | Inputs are implicit | Inputs are listed | Inputs include examples and blockers |
| Workflow Steps | Prose only | Steps exist | Steps map to phases, owners, and gates |
| Evidence Contract | Chat summary | Some artifacts | Durable artifacts plus ledger events |
| Stop Conditions | None | Some risks named | Stop/escalation gates are machine-checkable |
| Verification | Manual vibes | One check | Layered checks: artifact, event, dashboard, dispatch state |
| Reusability | One-off | Adaptable with edits | Template-ready and documented |
| Failure Modes | Unknown | Known issues listed | Failure modes have prevention gates |
| Token Discipline | No budget | Budget named | Budget has hard cap and defer policy |

Promotion guidance:

- 0-7: keep as research notes.
- 8-13: candidate skill; dogfood on one bounded task.
- 14-18: reusable workflow; add template, tutorial, and tests.

## Required Promotion Evidence

Before adding a skill to a public workflow template, register:

- `skill-evaluation-rubric.md`
- A dogfood run or tutorial.
- A verification report.
- At least one documented failure mode and mitigation.

The `skill_evaluation_rubric_exists` gate can enforce this evidence when a workflow is explicitly about skill creation or promotion.

