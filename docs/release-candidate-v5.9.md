# Release Candidate v5.9.0rc1

This document records the v5.9 release-candidate scope and stop conditions.

## Scope

v5.9.0rc1 includes:

- v5.4 open-source facade polish,
- v5.5 end-to-end workflow tutorials,
- v5.6 adapter extension readiness planning,
- v5.7 dashboard Operator Brief,
- v5.8 trial feedback intake,
- package version alignment for `5.9.0rc1`.

## Release Candidate Claim

Multi-CLI Orchestrator is ready for public Alpha trials by developers who understand that:

- it is local-first,
- it is evidence-gated,
- supervised execution is limited to adapters that pass readiness gates,
- manual-only adapters still require human operation,
- and automation authority is intentionally conservative.

## Not Claimed

The release candidate does not claim:

- production SaaS readiness,
- hosted team permissions,
- real concurrent provider execution,
- automatic support for every CLI,
- provider-account quota visibility,
- or autonomous long-running work without bounded loop caps.

## Final Gate Before Tagging

Before creating a public tag or GitHub release:

1. Run the full release verification commands.
2. Confirm GitHub CI passes on the release-candidate commit.
3. Confirm `README.md`, `CHANGELOG.md`, `ROADMAP.md`, and `pyproject.toml` agree on the release status.
4. Confirm no private paths, credentials, screenshots, or business data are present.
5. Decide whether to tag `v5.9.0rc1` or continue collecting trial feedback first.

## Hardening Added After RC Draft

- Public tutorial workflows are now covered by automated regression tests.
- The regression test completes `documentation-release-loop`, `frontend-review-loop`, and `adapter-onboarding-loop` with the same evidence labels documented in the tutorials.
- This prevents workflow template gates and tutorial commands from drifting silently.
- GitHub Actions workflow now uses Node 24-compatible `actions/checkout@v5` and `actions/setup-python@v6`.

## Recommended Next Step

Collect external trial feedback using the trial feedback issue template before promoting this RC to a stable release.
