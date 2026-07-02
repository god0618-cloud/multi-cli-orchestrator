# Release Notes v5.9.0rc1

v5.9.0rc1 is the public Alpha release candidate for Multi-CLI Orchestrator.

It does not add broader automation authority. It packages the v5 control-plane work into something easier to understand, try, contribute to, and give feedback on.

## Highlights

- README now opens with visual proof and clearer public positioning.
- Visual walkthrough links point to dashboard, replay, and adapter matrix screenshots.
- Three end-to-end tutorials show complete evidence-gated loops:
  - documentation release,
  - frontend review,
  - adapter onboarding.
- Adapter extension roadmap defines how Mimo Code and CodeWhale can move from manual-only to supervised readiness without skipping gates.
- Dashboard first screen now includes an Operator Brief and a next-command hint.
- Boss dashboard now has dependency-free Chinese/English switching, with README screenshots for both views.
- Trial feedback issue template and maintainer loop make external feedback reproducible and safe to triage.

## Safety Posture

The release candidate keeps the same safety posture:

- no arbitrary shell execution,
- no hidden writes to native CLI memory or stable knowledge bases,
- no auto-dispatch to manual-only adapters,
- no unbounded workflow loops,
- no implicit real provider smoke tests in CI.

## Verification

Expected release-candidate verification:

```bash
PYTHONPATH=src python3 -m unittest tests.unit.test_workspace
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mco.cli release check . --json
PYTHONPATH=src python3 -m mco.cli audit .
```

Additional v5.9 evidence:

- documentation, frontend, and adapter onboarding tutorials reached `recommended_action=complete` in temporary local workspaces,
- Mimo Code and CodeWhale scaffold kits passed generated contract tests and `mco adapter validate-kit`,
- issue template YAML files parsed successfully,
- dashboard smoke confirmed the Operator Brief, Next Command, and Chinese/English toggle render,
- GitHub Actions CI passed on the release-candidate commit.

## Known Limits

- Mimo Code and CodeWhale remain manual-only.
- Provider-account quota remains unknown unless task-local evidence supports a narrower claim.
- The dashboard is static HTML, not a hosted multi-user service.
- External trial feedback is still needed before claiming broader production readiness.
