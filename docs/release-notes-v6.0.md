# Release Notes v6.0.0a1

v6.0.0a1 is the expert-workflow productization Alpha for Multi-CLI Orchestrator.

It keeps the conservative v5 safety posture while making workflow templates more useful for real product work and less intimidating for single-agent users.

## Highlights

- Workflow templates can now carry manifests that explain trigger, scope, inputs, artifacts, verification, stop conditions, and failure modes.
- Manifest metadata supports:
  - `stack: single | dual`
  - `evidence_level: L1 | L2 | L3`
  - token `budget` with `avg_token_cost`, `hard_cap`, and `defer_policy`
- Added `prototype-brief-loop` for spec-first product/UI prototype work.
- Upgraded `frontend-review-loop` so implementation waits for prototype brief and plan review.
- Added semantic gates:
  - `prototype_brief_exists`
  - `plan_review_passed`
  - `browser_visual_evidence_registered`
  - `skill_evaluation_rubric_exists`
- Added a two-level skill evaluation rubric:
  - L1 admission: trigger, stop condition, token budget.
  - L2 promotion: workflow, evidence, verification, failure modes, token discipline.
- Added a compact community-note absorption template with four sections: what it says, reality check, signal, decision.

## Safety Posture

v6.0.0a1 does not loosen automation authority:

- no arbitrary shell execution,
- no hidden writes to native CLI memory or stable knowledge bases,
- no auto-dispatch to manual-only adapters,
- no unbounded workflow loops,
- no implicit real provider smoke tests in CI.

## User Posture

The default public posture is now explicit:

- single agent first,
- multi-CLI fanout only after plan review and adapter gates,
- L1 evidence by default,
- L2/L3 evidence only when the review scenario needs it,
- token budget visible before the controller context is burned.

## Verification

Expected verification:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mco.cli release check .
PYTHONPATH=src python3 -m mco.cli audit .
```

Regression coverage proves:

- workflow manifests persist into `plan.json`,
- invalid `stack`, `evidence_level`, and token budget metadata are rejected,
- `prototype-brief-loop` waits for plan-review evidence,
- prototype implementation waits for browser/visual evidence,
- source-tree and packaged workflow templates stay synchronized.

## Known Limits

- Mimo Code and CodeWhale remain manual-only.
- Provider-account quota remains unknown unless task-local evidence supports a narrower claim.
- The dashboard is static HTML, not a hosted multi-user service.
- v6.0.0a1 is an Alpha, not a stable production automation release.

