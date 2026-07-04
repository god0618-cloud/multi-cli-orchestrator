# Release Candidate v6.1.0a1

This document records the v6.1 Alpha scope and stop conditions.

## Scope

v6.1.0a1 includes:

- dispatch lease metadata,
- heartbeat command,
- stale dispatch reclaim command,
- max-attempt exhaustion behavior,
- Runtime Resilience dashboard visibility,
- run-ledger events for lease, heartbeat, reclaim, and exhaustion,
- regression tests for stale worker recovery.

## Alpha Claim

Multi-CLI Orchestrator can now recover from a claimed dispatch whose worker stopped reporting progress, as long as an operator or bounded automation runs `mco dispatch reclaim`.

## Not Claimed

The Alpha does not claim:

- always-on background daemon operation,
- workspace-global worker supervision,
- automatic provider-account quota visibility,
- or autonomous recovery that bypasses evidence gates.

## Final Gate Before Tagging

Before creating a public tag or GitHub release:

1. Run the full release verification commands.
2. Confirm GitHub CI passes on the Alpha commit.
3. Confirm `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `pyproject.toml`, and `src/mco/__init__.py` agree on `6.1.0a1`.
4. Confirm no private paths, credentials, screenshots, or business data are present.
5. Run the dispatch lease/reclaim regression test.
