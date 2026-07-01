# v5 Public Polish Loop

This loop turns the v5.0 strict-gate baseline into a clearer public Alpha release.

## Objective

Make Multi-CLI Orchestrator understandable, runnable, shareable, and contribution-ready without expanding execution authority.

## Loop Phases

| Phase | Goal | Gate |
| --- | --- | --- |
| v5.0-public-polish | Tighten public wording and remove stale release confusion | README, roadmap, overview, and archived draft state are clean |
| v5.1-demo-story | Add a visual and operational demo story | Fresh-clone demo, dashboard, adapter matrix, and replay assets exist |
| v5.2-dogfood-workflows | Prove the loop on realistic workflows | At least three realistic workflows produce ledger, artifacts, dashboard, replay, and close reports |
| v5.3-contributor-onramp | Make contribution paths obvious | Good-first issues, adapter maturity model, and contribution gates exist |

## Current Sprint: v5.0-public-polish

Acceptance:

- README no longer contains stale v4 baseline wording.
- ROADMAP is capability-led, not a misleading version ladder.
- Project overview does not frame speculative work as locked v6/v7 promises.
- Old v4 public-material drafts are archived away from the active docs surface.
- Tests, compile, release check, and audit pass.

## Operating Rule

Do not increase automation authority in this loop. Improve clarity, demos, evidence, and contribution paths first.

## v5.1-demo-story Acceptance

- `mco demo walkthrough` produces a public-safe demo bundle.
- Dashboard, replay, and adapter matrix screenshots exist without private user paths.
- A demo story document explains the narrative from prompt-copy pain to evidence-backed control plane.
- README links to the demo story.

## v5.2-dogfood-workflows Acceptance

- Three realistic workflow templates exist: documentation release, frontend review, and adapter onboarding.
- Templates are synced between source-tree templates and packaged templates.
- A realistic workflow examples README explains how to run and close one workflow with placeholder evidence.
- All three templates have been dogfooded to `recommended_action=complete` with placeholder evidence in a temporary workspace.
- No new provider execution authority is added.

## v5.3-contributor-onramp Acceptance

- Contribution docs reflect the current v5 posture.
- Good-first issue guidance exists.
- Adapter maturity levels and promotion gates are explicit.
- Workflow template contribution rules are explicit.
- Issue templates cover adapter requests, workflow requests, bugs, and safety concerns.

## v5.4-open-source-facade Acceptance

- README first screen includes a visual proof asset.
- README links to dashboard, replay, and adapter matrix visual walkthrough assets.
- Launch playbook reflects the current v5 public Alpha posture.
- GitHub topics and repo description match the project positioning.
- Public launch language avoids unsafe automation claims.

## v5.5-end-to-end-cases Acceptance

- Documentation release, frontend review, and adapter onboarding tutorials exist.
- Each tutorial includes workflow template, phase evidence, close criteria, and common failure modes.
- Tutorial commands use temporary workspaces and avoid private local paths.
- README links to the tutorial index.
- Tutorials describe bounded evidence gates instead of promising unsupervised automation.
