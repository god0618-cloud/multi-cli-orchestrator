# Multi-CLI Orchestrator

Local-first Agent OS for coordinating multiple AI coding CLIs as supervised workstations.

Multi-CLI Orchestrator is not another single-runtime agent framework. It is a coordination layer for people who already use multiple AI coding CLIs and want them to share task state, workflow gates, evidence artifacts, run replay, and a boss dashboard.

## Status

This repository is in v1.5 supervised-adapter stage. The current baseline is a clean open-source MVP with no private paths, no private business data, a runnable hello workflow, generic dispatch primitives, replayable evidence, adapter sandbox gates, scriptable CLI output, CI smoke gates, release checks, disabled adapter templates, a deliberately narrow real-execution path for safe commands, and one real first-party supervised adapter for Claude Code prompt execution.

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
mco orchestrate-start <task_id> --template frontend-review-loop
mco dashboard <task_id>
mco usage snapshot <task_id>
mco run replay <path-to-RUN_LEDGER.json>
```

Implemented in this v1.5 baseline:

- `mco init`
- `mco doctor`
- `mco task create`
- `mco task list`
- `mco task status`
- `mco task event`
- `mco artifact register`
- `mco adapter capabilities`
- `mco adapter doctor`
- `mco dispatch queue/list/claim/complete`
- `mco dispatch execute --dry-run`
- `mco dispatch execute --command-json`
- `mco dispatch execute --agent claude-code --prompt-file`
- `mco dashboard`
- `mco orchestrate-start`
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
mco task list --workspace .mco-workspace
mco orchestrate-start "Hello orchestrated task" --template hello-multi-cli --workspace .mco-workspace
mco demo hello-multi-cli --workspace .mco-demo
mco audit .
mco release check .
```

## v1.5 Command Matrix

| Command | Status |
| --- | --- |
| `mco init` | implemented |
| `mco doctor` | implemented |
| `mco task create` | implemented |
| `mco task create --json` | implemented |
| `mco task list` | implemented |
| `mco task status` | implemented |
| `mco task event` | implemented |
| `mco artifact register` | implemented |
| `mco adapter capabilities` | `generic-cli`, `claude-code` |
| `mco adapter doctor` | generic and Claude Code readiness checks |
| `mco dispatch queue/list/claim/complete` | generic local queue |
| `mco dispatch execute --dry-run` | sandbox/capability gate validation |
| `mco dispatch execute --command-json` | safe command execution with sandbox, allowlist, timeout, and evidence report |
| `mco dispatch execute --agent claude-code --prompt-file` | bounded Claude Code prompt execution with no tools, no session persistence, budget cap, timeout, and transcript artifact |
| `mco dashboard` | implemented |
| `mco usage snapshot` | task-local usage/quota evidence rollup |
| `mco orchestrate-start` | bounded initializer |
| `mco schema validate` | implemented |
| `mco serve` | implemented |
| `mco audit` | implemented |
| `mco demo hello-multi-cli` | implemented |
| `mco run replay` | implemented |
| `mco release check` | implemented |
| arbitrary shell execution | intentionally not implemented |
| first-party CLI adapters | Claude Code implemented; Kimi/Mimo/CodeWhale still disabled |
| run replay UI | not implemented |

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
- `docs/release-checklist.md`

## Safety Defaults

- No default writes outside the configured workspace.
- No default writes to native CLI memory, stable knowledge bases, or profile files.
- No destructive action without an explicit future gate.
- No arbitrary shell execution. Generic execution only allows narrowly validated commands such as `echo ...` and print-only `python -c ...`.
- Claude Code execution is bounded to `claude --print`, tools disabled, session persistence disabled, task-local prompt files, timeout/output limits, and an explicit budget cap.
- Usage snapshots are evidence-derived. They aggregate task-local execution reports and dispatch records; they do not claim provider-account quota unless that evidence exists.
- No private local paths or business data should be committed.

## License

Apache-2.0, provisional for the extraction baseline.
