# Adapter Contributor Guide

New adapter work starts disabled.

The goal is to prove the contract before connecting a real provider CLI. A useful adapter contribution should show:

- capability manifest
- sandbox contract
- fake CLI test fixture
- deterministic contract tests
- doctor checks
- bounded non-interactive execution
- task-local execution report
- usage/quota evidence
- explicit opt-in smoke command

Start with:

```bash
mco adapter scaffold my-cli --output-dir adapter-kits/my-cli
cd adapter-kits/my-cli
mco schema validate adapter-manifest my-cli.adapter.json
mco schema validate sandbox-contract my-cli.sandbox.json
python -m unittest test_my_cli_adapter_contract.py
mco adapter validate-kit .
```

Promotion rule:

Do not mark an adapter as supervised until the fake fixture, doctor checks, execution report, usage evidence, and opt-in real smoke gate all pass. Real provider calls must never run in CI unless a maintainer explicitly opts in.

Review checklist:

- The adapter starts disabled.
- Quota is `unknown` unless the CLI exposes reliable local evidence or a per-run budget cap.
- Prompts or commands are bounded by timeout and output size.
- Prompt files, reports, and artifacts stay inside the task workspace.
- Native CLI memory/profile files are not modified.
- Stable knowledge bases are not modified.
- Smoke tests write task-local evidence and verify a fixed sentinel.
