# Contributing

Multi-CLI Orchestrator is a local-first control plane for coordinating AI coding CLIs. Contributions are welcome when they keep the project evidence-backed, bounded, and safe by default.

## Contribution Principles

- Keep core behavior local-first and adapter-neutral.
- Add tests for new command behavior.
- Never commit private paths, credentials, screenshots with personal paths, or business data.
- Prefer generic examples that produce visible artifacts.
- Keep workflow claims evidence-backed.
- Keep command output scriptable for automation paths.
- Any execution feature must fail closed without sandbox evidence.
- Do not increase provider execution authority without adapter readiness, quota, timeout, smoke, and artifact evidence.

## Good Starting Points

Read:

- [`docs/GOOD_FIRST_ISSUES.md`](docs/GOOD_FIRST_ISSUES.md)
- [`docs/ADAPTER_MATURITY_MODEL.md`](docs/ADAPTER_MATURITY_MODEL.md)
- [`docs/WORKFLOW_TEMPLATE_CONTRIBUTING.md`](docs/WORKFLOW_TEMPLATE_CONTRIBUTING.md)
- [`docs/adapter-contributor-guide.md`](docs/adapter-contributor-guide.md)

## Before Opening a PR

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.unit.test_workspace
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m mco.cli release check . --json
PYTHONPATH=src python3 -m mco.cli audit .
```

If your change adds public docs or screenshots, also run a private path scan:

```bash
rg -n "/Users/|private-vault-name|private-task-state-path" README.md docs examples templates src tests || true
```

## Adapter Contributions

New adapters must start disabled. Do not open a PR that marks an adapter supervised unless the maturity gates are met.

Generate a kit:

```bash
mco adapter scaffold my-cli --output-dir adapter-kits/my-cli
cd adapter-kits/my-cli
python -m unittest test_my_cli_adapter_contract.py
mco adapter validate-kit .
```

See [`docs/ADAPTER_MATURITY_MODEL.md`](docs/ADAPTER_MATURITY_MODEL.md).

## Workflow Template Contributions

Workflow templates must be bounded and evidence-gated. Add templates to both:

- `templates/workflows/`
- `src/mco/templates/workflows/`

Then prove they load through `mco orchestrate-start` and can reach a clear `wait`, `escalate`, or `complete` state.

See [`docs/WORKFLOW_TEMPLATE_CONTRIBUTING.md`](docs/WORKFLOW_TEMPLATE_CONTRIBUTING.md).

## Safety Reviews

Open a safety concern when a change might affect:

- arbitrary command execution,
- provider cost or quota,
- native CLI memory/profile files,
- stable knowledge bases,
- private path or credential exposure,
- auto-dispatch behavior,
- workflow loop stop conditions.
