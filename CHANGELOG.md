# Changelog

## 3.2.0

- Added `mco run replay --html <path>` for dependency-free static replay pages.
- Walkthrough bundles now include `RUN_REPLAY.html`.
- Added regression coverage for replay HTML generation.

## 3.1.0

- Added `mco demo walkthrough` to generate a complete public walkthrough bundle.
- The walkthrough writes a replay transcript, dashboard reference, generated adapter kit, README, and summary JSON.
- Added regression coverage that the generated walkthrough adapter contract test passes.

## 3.0.0

- Promoted the project to an open-source MVP release baseline.
- Added package metadata for license, keywords, Python classifiers, and public project URLs.
- Added `docs/launch-playbook.md` and `docs/release-notes-v3.0.md` for public launch and release operations.
- Updated the README first screen around external-user value, status, and command coverage.
- Added a packaged Kimi Code supervised sandbox contract that was previously present only in the source-tree templates.
- Added regression coverage to keep source-tree templates and packaged templates synchronized.

## 2.8.0

- Expanded `mco adapter scaffold` into a contributor-ready adapter kit.
- Scaffold output now includes README guidance, a deterministic fake CLI fixture, and a unittest contract template.
- Added `docs/adapter-contributor-guide.md` for adapter promotion expectations and review gates.
- Added regression coverage that generated adapter contract tests pass.

## 2.7.0

- Added workflow phase state to generated `plan.json` files.
- Added `mco workflow status <task_id>` to inspect current phase and phase states.
- Added `mco workflow advance <task_id>` with gate evaluation, pass/fail verdicts, fail-stop behavior, and optional `--auto-dispatch`.
- Auto-dispatch can reuse adapter readiness gates through `--require-ready`.

## 2.6.0

- Added `mco monitor <task_id>` to write bounded task status snapshots as evidence.
- Monitor snapshots are registered in `RUN_LEDGER.json` and stored under task-local `artifacts/status-snapshots/`.
- Added `--cycles`, `--interval-seconds`, `--audit`, and `--doctor` flags with hard upper bounds.
- Kept provider probing explicit via `--doctor`; default monitor cycles use the lightweight status baseline.

## 2.5.0

- Added `mco status --doctor` for explicit local adapter probing.
- Status JSON now includes `doctor_probe`, `doctor_status`, and `doctor_check_count` so automation can distinguish policy baseline from real local checks.
- Kept default `mco status` lightweight and free of external CLI/auth probing.
- Added regression coverage proving fake Claude Code and Kimi Code adapters become `READY_SUPERVISED` only when `--doctor` is requested.

## 2.4.0

- Added `mco status` as a compact operator summary for the workspace.
- The status command defaults to the latest task and summarizes dispatch counts, the latest dispatch, adapter readiness, quota semantics, and gate posture.
- Added `mco status --json` for automation and `mco status --audit` for one-line audit counts.
- Kept status rendering free of provider doctor probing so routine operator checks do not consume external CLI/auth calls.

## 2.3.0

- Integrated the adapter matrix into the task dashboard.
- Added a dashboard Dispatch Gate Status section showing `--require-ready` gate evidence.
- Dashboard now distinguishes policy baseline from local doctor probing to avoid implicit provider checks during page rendering.
- Added regression coverage for blocked dispatch visibility in dashboard HTML.

## 2.2.0

- Added adapter gate evaluation for dispatch queueing.
- Added `mco dispatch queue --require-ready` to block auto-dispatch unless the adapter matrix reports `READY_SUPERVISED`.
- Blocked dispatches now write durable evidence with `status=blocked`, gate reason, and no inbox file.
- Added tests proving disabled adapters do not enter an inbox and ready supervised adapters do.

## 2.1.0

- Added `mco adapter matrix` to show a machine-readable readiness and promotion matrix for known adapters.
- Added optional `mco adapter matrix --doctor` probing for implemented adapters.
- Added `--output` and `--html` flags so teams can publish adapter readiness as JSON and static boss-view HTML.
- The matrix distinguishes implemented adapters from disabled templates, exposes quota semantics, smoke-gate availability, per-run budget-cap support, and promotion blockers.

## 2.0.0

- Added the second supervised first-party adapter: `kimi-code`.
- Added Kimi Code capability and doctor checks, including binary discovery, prompt-mode flag checks, and `kimi doctor`.
- Added `mco dispatch execute --agent kimi-code --prompt-file ...` for bounded `kimi --prompt` execution with task-local prompt files, timeout, output truncation, and execution report artifacts.
- Added `mco adapter smoke kimi-code` as an explicit opt-in real-adapter smoke command with a sentinel evidence bundle.
- Added a `kimi-code-supervised` sandbox contract template using host CLI auth only and task-workspace read/write boundaries.
- Kept Kimi quota status honest as `unknown`; unlike Claude Code, this adapter currently has no provider-budget cap flag.

## 1.9.0

- Added `mco adapter scaffold <agent>` to generate disabled adapter onboarding files.
- Scaffold output includes adapter manifest, sandbox contract draft, and smoke checklist.
- New adapters remain disabled by default until capability, sandbox, quota, non-interactive execution, evidence reporting, and smoke gates are proven.
- Added overwrite protection unless `--force` is passed.

## 1.8.0

- Added `mco adapter smoke claude-code` as an explicit real-adapter regression command.
- The smoke command creates a task-local evidence bundle: sandbox contract, prompt, dispatch, Claude execution report, usage snapshot, dashboard, and adapter smoke result.
- Added a fixed sentinel check so successful process execution alone is not enough; Claude output must contain `MCO_ADAPTER_SMOKE_OK`.
- Capped smoke-test budget at `--max-budget-usd <= 0.25`, defaulting to `0.05`.
- Kept real smoke tests opt-in and outside CI; unit tests use a fake Claude binary.

## 1.7.0

- Added `mco usage snapshot <task_id>` to generate a task-local `USAGE_SNAPSHOT.json`.
- Added a durable usage/quota evidence contract derived only from dispatch records and registered execution reports.
- Aggregated per-agent dispatch counts, observed cost, budget caps, estimated remaining budget, quota status, and last error.
- Added usage snapshot visibility to the boss dashboard.
- Explicitly labels provider-account quota as unknown unless task-local evidence supports a narrower claim.

## 1.6.0

- Upgraded the static dashboard into a boss-view control room.
- Added adapter readiness summaries grouped by agent, including dispatch counts and latest execution report status.
- Surfaced supervised Claude Code budget usage and remaining budget from execution reports.
- Added an owner escalation queue for blocked/failed dispatches and structured adapter errors.
- Kept the dashboard dependency-free and task-local so public demos remain easy to clone and run.

## 1.5.0

- Added the first real supervised first-party adapter: `claude-code`.
- Added Claude Code capability and doctor checks, including binary discovery, required non-interactive flags, and auth status verification.
- Added `mco dispatch execute --agent claude-code --prompt-file ...` for bounded `claude --print` execution with no tools, no session persistence, timeout, output truncation, and budget cap.
- Added Claude execution reports with prompt hash, stdout/stderr transcript, success/failure classification, and run-ledger artifact registration.
- Added fail-safe handling for structured Claude budget errors such as `error_max_budget_usd`.
- Added a `claude-code-supervised` sandbox contract template using host CLI auth only and task-workspace read/write boundaries.
- Kept arbitrary shell execution and other first-party adapters disabled.

## 1.2.0

- Added release readiness issue templates and pull request template.
- Added reusable Mermaid diagram assets.
- Added local git readiness as part of release check reporting.
- Release check reports generated Python/package cache files as WARN instead of FAIL so editable-install users are not blocked by local cache artifacts.

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
