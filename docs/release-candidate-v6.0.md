# Release Candidate v6.0.0a1

This document records the v6.0 Alpha scope and stop conditions.

## Scope

v6.0.0a1 includes:

- workflow template manifests,
- `stack`, `evidence_level`, and token `budget` metadata,
- semantic gates for prototype brief, plan review, browser/visual evidence, and skill rubric evidence,
- `prototype-brief-loop`,
- upgraded `frontend-review-loop`,
- L1/L2 skill evaluation rubric,
- four-section note absorption template,
- documentation updates across README, Roadmap, command reference, quickstart, workflow schema, and tutorials,
- package version alignment for `6.0.0a1`.

## Alpha Claim

Multi-CLI Orchestrator is ready for public Alpha trials by developers who understand that:

- it is local-first,
- it is evidence-gated,
- single-agent workflows are the default path,
- multi-CLI fanout is gated and optional,
- manual-only adapters still require human operation,
- and automation authority remains conservative.

## Not Claimed

The Alpha does not claim:

- production SaaS readiness,
- hosted team permissions,
- real concurrent provider execution,
- automatic support for every CLI,
- provider-account quota visibility,
- or autonomous long-running work without bounded loop caps.

## Final Gate Before Tagging

Before creating a public tag or GitHub release:

1. Run the full release verification commands.
2. Confirm GitHub CI passes on the Alpha commit.
3. Confirm `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `pyproject.toml`, and `src/mco/__init__.py` agree on `6.0.0a1`.
4. Confirm no private paths, credentials, screenshots, or business data are present.
5. Collect feedback from at least one fresh-clone tutorial run.

