# Changelog

## 1.2.0

- Added release readiness issue templates and pull request template.
- Added reusable Mermaid diagram assets.
- Added local git readiness as part of release check reporting.

## 1.1.0

- Added `mco task create --json` for script-safe automation.
- Added disabled-by-default first-party adapter manifest templates.
- Added adapter manifest schema validation from the CLI.
- Added `mco release check` for release readiness automation.
- Added release checklist, architecture diagrams, and multi-CLI rationale docs.
- Hardened CI with demo smoke, safe execution smoke, unsafe command smoke, and package audit.
- Updated roadmap and contribution guidance for release-hardening posture.

## 1.0.0

- Added supervised safe command execution for `generic-cli`.
- Added command allowlist validation for `echo ...` and print-only `python -c ...`.
- Added execution reports with stdout/stderr capture, truncation flags, timeout handling, and dispatch failure status.
- Kept arbitrary shell execution and first-party CLI adapters out of scope until stronger adapter manifests and quota checks exist.

## 0.8.0

- Added adapter doctor readiness states for `generic-cli`.
- Added sandbox gate enforcement for supervised dry-run dispatch execution.
- Added `mco dispatch execute --dry-run`, including fail-closed behavior when sandbox evidence is missing.

## 0.5.0

- Added v0.5 generic adapter manifest and dispatch queue lifecycle.
- Added executable hello demo, CI workflow draft, and provisional Apache-2.0 license.
- Added package install compatibility for editable installs and packaged workflow templates.
- Added read-only `mco run replay` for `RUN_LEDGER.json` timeline inspection.

## 0.2.0

- Created clean open-source extraction skeleton.
- Added `mco init` and `mco doctor`.
- Added `mco task create`, `mco task list`, and `mco dashboard`.
- Added `mco task status`, `mco task event`, `mco artifact register`, and `mco audit`.
- Added `mco orchestrate-start`, workflow template loading, schema validation, and hello demo.
- Added command reference and v0.2 close hardening tests.
- Added loop spec and run ledger templates.
- Added redaction checklist and extraction map.
