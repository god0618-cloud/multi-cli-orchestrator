# Roadmap

Multi-CLI Orchestrator is currently at the v5.9.0rc1 public Alpha release-candidate baseline.

This roadmap is intentionally capability-led rather than hype-version-led. The project should advance only when a capability is backed by tests, evidence artifacts, and clear safety boundaries.

## Current Baseline: v5.9 RC

The v5.9 RC baseline is a credible Alpha release candidate for developers who want to experiment with local-first multi-CLI orchestration.

Completed capabilities:

- Local task workspace with `LOOP_SPEC.json`, `RUN_LEDGER.json`, `plan.json`, dispatch inboxes, and evidence artifacts.
- Generic task lifecycle: create, list, status, event, artifact registration, audit, and release check.
- Dispatch queue: queue, claim, complete, blocked evidence, and bounded dispatch waves.
- Adapter layer: generic CLI, Claude Code, and Kimi Code supervised paths; Mimo Code and CodeWhale-style CLIs remain manual-only unless future gates prove otherwise.
- Adapter visibility: capabilities, doctor, matrix, scaffold, validate-kit, and explicit smoke commands.
- Safety posture: no arbitrary shell execution, no silent native memory writes, no unbounded provider execution, no infinite workflow loop.
- Workflow gates: task-local files, registered artifacts, ledger events, user decisions, dispatch terminal state, failed/blocked dispatch absence, and dispatch status counts.
- Bounded workflow automation: `mco workflow observe` and `mco workflow loop --max-steps`.
- `strict-self-closing` template: `plan -> execute -> verify -> close`.
- Operator surfaces: `mco status`, `mco monitor`, static boss dashboard, usage snapshot, run replay, and walkthrough demo.
- CI coverage, release check, and audit gates.
- Public launch facade with visual walkthrough assets.
- Three end-to-end tutorials: documentation release, frontend review, and adapter onboarding.
- Adapter extension roadmap for manual-only CLIs such as Mimo Code and CodeWhale.
- Trial feedback loop and GitHub issue template for external evaluation.

Known maturity level:

- Engineering core: Alpha, credible for early adopters.
- Public onboarding: usable, but still being polished.
- Production automation: intentionally conservative; not advertised as a fully autonomous execution system.

## Completed v5 Public Polish

Goal: make the project easier to understand, try, and share without changing the safety posture.

- Tightened README first-screen positioning.
- Kept public materials versioned and archived stale launch drafts.
- Added a clear "when to use / when not to use" section.
- Added a short demo story that shows the value without requiring users to read every schema document.
- Added screenshots for dashboard, adapter matrix, and replay.
- Linked complete project overview, tutorial index, contributor onramp, and trial feedback loop from README.

Acceptance bar:

- A new developer can understand the project in one minute.
- A new developer can run a local demo in five minutes.
- Public docs do not mix old v4 wording with v5 capability claims.

## Demo Story Track

Goal: make the project visually and operationally demonstrable.

Target assets:

- Terminal walkthrough script.
- Dashboard screenshot.
- Adapter matrix screenshot.
- Replay HTML sample.
- One realistic workflow bundle, not just a hello task.

Acceptance bar:

- The demo can be posted with the GitHub link and still communicate the value.
- The demo can run from a fresh clone without private local paths or business data.
- The demo shows why the loop advances, waits, escalates, or completes.

## Dogfood Workflow Track

Goal: prove the orchestration model on realistic tasks before adding broader automation.

Candidate workflows:

- Documentation release loop: plan -> write -> verify -> close.
- Frontend review loop: implement -> screenshot -> visual review -> close.
- Adapter onboarding loop: scaffold -> validate -> smoke -> promote or reject.

Acceptance bar:

- Each workflow produces `LOOP_SPEC.json`, `RUN_LEDGER.json`, artifacts, dashboard, replay, and close report.
- At least one real defect or workflow gap is found and fixed through dogfooding.
- Workflow templates stay bounded and auditable.

## Contributor Onramp Track

Goal: make outside contribution practical.

Planned assets:

- Good first issues list.
- Adapter maturity model.
- Workflow template contribution guide.
- Example adapter request and review path.
- Clear promotion gates from disabled adapter to supervised adapter.

Acceptance bar:

- A contributor can request a new adapter with the right evidence.
- A contributor can generate and validate an adapter kit locally.
- Maintainers can reject unsafe adapters with a documented reason instead of a subjective judgment.

## Next Candidate Track

Goal: move from Alpha RC to broader external adoption evidence.

Candidate work:

- Collect at least three sanitized trial feedback reports.
- Add one more adapter kit based on external evidence, but keep it disabled until gates pass.
- Add dashboard screenshots after the v5.7 Operator Brief.
- Add a public demo GIF or short video if it can be produced without private data.
- Tighten docs around installation on macOS/Linux/Windows.

Acceptance bar:

- External users can reproduce at least one tutorial without maintainer hand-holding.
- Trial feedback closes through the documented loop.
- No safety boundary is loosened for marketing reasons.

## Medium-Term Exploration

Explore only after the near-term polish and dogfood tracks are stable:

- Stronger quota, cost, cancel, and timeout contracts.
- Better conflict governance for concurrent worker outputs.
- Optional long-term memory promotion gates.
- Multi-project workspace management.
- More capable dashboards without introducing heavy runtime requirements.

## Long-Term Vision

The long-term direction is a local-first Agent OS control plane:

- AI CLIs remain independent workstations.
- The orchestrator manages task state, workflow gates, evidence, replay, safety, and escalation.
- Human users intervene only at real decision gates.
- Automation earns more authority only after adapter readiness, sandbox, quota, and smoke evidence prove it is safe.

This is a direction, not a locked version promise.
