# Multi-CLI Orchestrator

Local-first Agent OS for coordinating multiple AI coding CLIs as supervised workstations.

Multi-CLI Orchestrator is not another single-runtime agent framework. It is a coordination layer for people who already use multiple AI coding CLIs and want them to share task state, workflow gates, evidence artifacts, run replay, and a boss dashboard.

## What It Gives You

- A local task workspace with `LOOP_SPEC.json`, `RUN_LEDGER.json`, `plan.json`, dispatch inboxes, and artifact evidence.
- Supervised CLI workstations instead of hidden subagents: Claude Code and Kimi Code can run through bounded adapters when installed and authenticated.
- Fail-stop workflow gates so phases advance only after evidence is written.
- A dependency-free boss dashboard for status, adapter readiness, dispatch gates, usage snapshots, artifacts, and timeline.
- Disabled-by-default adapter kits for adding new CLIs without pretending they are production-ready on day one.

## Status

This repository is at v5.0 strict-gate self-closing loop status. The baseline is clean of private paths and private business data, installable from a public clone, covered by CI smoke gates, and backed by release checks. It includes a runnable hello workflow, generic dispatch primitives, bounded multi-worker dispatch waves, replayable evidence, adapter sandbox gates, scriptable CLI output, disabled adapter scaffolding, a deliberately narrow real-execution path for safe commands, two supervised first-party prompt adapters, adapter gate visibility, compact operator status, explicit doctor probing, bounded monitor snapshots, dynamic workflow gates, bounded observe/advance loops, a strict self-closing workflow template, and contributor-ready adapter kits.

## Start Here

- New to the idea? Read [`docs/project-overview-v5.0.md`](docs/project-overview-v5.0.md).
- Want the shortest setup path? Run the [Quick Start](#quick-start).
- Want to see the operator surface? Generate a dashboard with `mco dashboard <task_id>`.
- Want to add a CLI? Start from [`docs/adapter-contributor-guide.md`](docs/adapter-contributor-guide.md).

## Should You Use It?

Use it when:

- You already use multiple AI coding CLIs and want shared task state instead of copy-pasted prompts.
- You need evidence artifacts, run replay, and phase gates before accepting AI-generated work.
- You want a local-first control plane that keeps automation bounded and visible.

Do not use it when:

- You want an all-powerful autonomous agent with unconstrained shell access.
- You expect every CLI to be auto-dispatched before adapter readiness, quota, sandbox, and smoke evidence exist.
- You need a hosted SaaS, production secrets manager, or organization-wide permission system today.

## Core Ideas

- **CLIs are workstations**: Codex, Claude Code, Kimi Code, and generic CLIs can all become supervised workers.
- **Loops beat prompts**: every orchestrated task needs a `LOOP_SPEC.json`.
- **Sandboxes before parallelism**: every worker needs an explicit `SANDBOX_CONTRACT.json` before parallel work.
- **Evidence before claims**: tasks close through artifacts, tests, screenshots, reports, or other durable evidence.
- **Replay before memory**: `RUN_LEDGER.json` preserves what happened before any long-term summary is promoted.
- **Boss dashboard**: the human should see who is working, what is blocked, and what needs a decision.

## Target CLI

```bash
mco init
mco doctor
mco task create "Build a mobile-first project page"
mco status
mco status --doctor
mco monitor <task_id> --cycles 3 --interval-seconds 10
mco orchestrate-start <task_id> --template frontend-review-loop
mco workflow status <task_id>
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
mco workflow advance <task_id> --phase plan --verdict pass --summary "Plan checked" --auto-dispatch
mco dashboard <task_id>
mco usage snapshot <task_id>
mco adapter matrix --doctor --output adapter-matrix.json --html adapter-matrix.html
mco dispatch queue <task_id> --agent kimi-code --title "Frontend pass" --instructions "..." --require-ready
mco dispatch wave <task_id> --spec wave.json --require-ready
mco adapter smoke claude-code --workspace .mco-workspace --max-budget-usd 0.05
mco adapter smoke kimi-code --workspace .mco-workspace
mco adapter scaffold kimi-code --output-dir adapter-kits/kimi-code
mco adapter validate-kit adapter-kits/kimi-code
mco demo walkthrough --workspace .mco-walkthrough --output-dir .mco-walkthrough-output
mco run replay <path-to-RUN_LEDGER.json>
mco run replay <path-to-RUN_LEDGER.json> --html replay.html
```

Implemented in this v5.0 baseline:

- `mco init`
- `mco doctor`
- `mco status`
- `mco monitor`
- `mco task create`
- `mco task list`
- `mco task status`
- `mco task event`
- `mco artifact register`
- `mco adapter capabilities`
- `mco adapter doctor`
- `mco adapter matrix`
- `mco adapter scaffold`
- `mco adapter validate-kit`
- `mco adapter smoke`
- `mco dispatch queue/list/claim/complete`
- `mco dispatch wave`
- `mco dispatch execute --dry-run`
- `mco dispatch execute --command-json`
- `mco dispatch execute --agent claude-code --prompt-file`
- `mco dispatch execute --agent kimi-code --prompt-file`
- `mco dashboard`
- `mco orchestrate-start`
- `mco workflow status/advance`
- `mco schema validate`
- `mco audit`

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
mco init --workspace .mco-workspace
mco doctor --workspace .mco-workspace
mco task create "Hello multi-CLI" --workspace .mco-workspace
mco status --workspace .mco-workspace
mco task list --workspace .mco-workspace
mco orchestrate-start "Hello orchestrated task" --template hello-multi-cli --workspace .mco-workspace
mco orchestrate-start "Strict product task" --template strict-self-closing --workspace .mco-workspace
mco demo hello-multi-cli --workspace .mco-demo
mco audit .
mco release check .
```

## v5.0 Command Matrix

| Command | Status |
| --- | --- |
| `mco init` | implemented |
| `mco doctor` | implemented |
| `mco status` | compact workspace, latest task, dispatch, adapter gate, optional audit summary, and explicit `--doctor` probe |
| `mco monitor` | bounded status snapshot loop that writes task-local evidence artifacts |
| `mco task create` | implemented |
| `mco task create --json` | implemented |
| `mco task list` | implemented |
| `mco task status` | implemented |
| `mco task event` | implemented |
| `mco artifact register` | implemented |
| `mco adapter capabilities` | `generic-cli`, `claude-code`, `kimi-code` |
| `mco adapter doctor` | generic, Claude Code, and Kimi Code readiness checks |
| `mco adapter matrix` | adapter readiness, execution mode, automation posture, quota, smoke, and promotion-blocker matrix |
| `mco adapter scaffold` | disabled adapter onboarding kit with README, fake CLI fixture, and unittest template |
| `mco adapter validate-kit` | CI-friendly validation for generated adapter contributor kits |
| `mco adapter smoke` | explicit opt-in real Claude Code or Kimi Code smoke test |
| `mco dispatch queue/list/claim/complete` | generic local queue |
| `mco dispatch queue --require-ready` | blocks auto-dispatch unless adapter readiness is `READY_SUPERVISED` |
| `mco dispatch wave` | bounded multi-worker dispatch wave; queues up to six worker dispatches and writes a wave manifest |
| `mco dispatch wave --require-ready` | applies adapter readiness gates to every worker and records blocked workers as evidence |
| `mco dispatch execute --dry-run` | sandbox/capability gate validation |
| `mco dispatch execute --command-json` | safe command execution with sandbox, allowlist, timeout, and evidence report |
| `mco dispatch execute --agent claude-code --prompt-file` | bounded Claude Code prompt execution with no tools, no session persistence, budget cap, timeout, and transcript artifact |
| `mco dispatch execute --agent kimi-code --prompt-file` | bounded Kimi Code prompt execution with timeout, output cap, and transcript artifact |
| `mco dashboard` | static boss view with control room, adapter matrix, dispatch gate status, usage, artifacts, and timeline |
| `mco usage snapshot` | task-local usage/quota evidence rollup |
| `mco orchestrate-start` | bounded initializer |
| `mco workflow status/observe/loop/advance` | phase state, machine next-action recommendation, bounded self-closing loop, and fail-stop advancement |
| `mco schema validate` | implemented |
| `mco serve` | implemented |
| `mco audit` | implemented |
| `mco demo hello-multi-cli` | implemented |
| `mco demo walkthrough` | complete public walkthrough bundle with replay transcript, dashboard, and adapter kit |
| `mco run replay` | text, JSON, and static HTML replay |
| `mco release check` | implemented |
| arbitrary shell execution | intentionally not implemented |
| strict self-closing workflow | `strict-self-closing` template with plan -> execute -> verify -> close evidence gates |
| first-party CLI adapters | Claude Code and Kimi Code implemented; Mimo/CodeWhale still manual-only/disabled for auto-dispatch |
| real concurrent provider execution | intentionally not implemented; v5.0 keeps execution bounded by adapter gates, workflow gates, and explicit loop caps |

## Repository Layout

```text
docs/                 Product, schema, architecture, and security docs
src/mco/              Python package
templates/            Workflow, loop, and sandbox templates
examples/             Artifact-producing examples
tests/                Unit and e2e checks
```

Useful docs:

- `docs/why-multi-cli.md`
- `docs/diagrams.md`
- `docs/adapter-templates.md`
- `docs/adapter-contributor-guide.md`
- `docs/launch-playbook.md`
- `docs/release-notes-v5.0.md`
- `docs/release-notes-v3.0.md`
- `docs/release-checklist.md`

## Safety Defaults

- No default writes outside the configured workspace.
- No default writes to native CLI memory, stable knowledge bases, or profile files.
- No destructive action without an explicit future gate.
- No arbitrary shell execution. Generic execution only allows narrowly validated commands such as `echo ...` and print-only `python -c ...`.
- Claude Code execution is bounded to `claude --print`, tools disabled, session persistence disabled, task-local prompt files, timeout/output limits, and an explicit budget cap.
- Claude Code smoke testing is explicit opt-in via `mco adapter smoke claude-code`; it may consume provider budget and writes a task-local evidence bundle.
- Kimi Code execution is bounded to `kimi --prompt`, task-local prompt files, timeout/output limits, and transcript artifacts.
- Kimi Code smoke testing is explicit opt-in via `mco adapter smoke kimi-code`; it may consume provider budget. Provider quota remains `unknown` because Kimi Code does not expose a Claude-style per-run budget cap in the current command contract.
- New adapter onboarding starts disabled via `mco adapter scaffold`; promotion requires capability, sandbox, quota, execution evidence, and smoke gates.
- Auto-dispatch paths should use `mco dispatch queue --require-ready`; non-ready adapters become blocked evidence and do not receive inbox files.
- Multi-worker paths should use `mco dispatch wave --require-ready`; the wave is capped at six workers and each worker still passes through the same adapter gates.
- Workflow automation should use `mco workflow observe` or `mco workflow loop`; loops are bounded by `--max-steps`, wait on missing evidence, and escalate on blocked/failed dispatches or missing user decisions.
- Usage snapshots are evidence-derived. They aggregate task-local execution reports and dispatch records; they do not claim provider-account quota unless that evidence exists.
- No private local paths or business data should be committed.

## License

Apache-2.0, provisional for the extraction baseline.
