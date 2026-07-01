from __future__ import annotations

import json
import re
from pathlib import Path


AGENT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def validate_agent_name(agent: str) -> None:
    if not AGENT_RE.match(agent):
        raise ValueError("agent must be 2-63 chars of lowercase letters, numbers, and dashes")


def disabled_manifest(agent: str) -> dict:
    return {
        "schema": "mco.adapter_manifest.v1.2",
        "agent": agent,
        "adapter_type": "first-party-disabled",
        "interactive": True,
        "non_interactive": False,
        "supervised": False,
        "can_read_inbox": False,
        "can_write_artifacts": False,
        "can_run_shell": False,
        "can_use_browser": False,
        "quota_status": "unknown",
        "safe_command_allowlist": [],
        "blocked_until": [
            "capability manifest reviewed",
            "sandbox contract reviewed",
            "quota preflight defined",
            "non-interactive command contract implemented",
            "execution evidence reporter implemented",
            "opt-in smoke gate implemented",
        ],
    }


def sandbox_draft(agent: str) -> dict:
    return {
        "schema": "mco.sandbox_contract.v0.2",
        "worker_id": f"{agent}-supervised-worker",
        "agent": agent,
        "write_scope": ["task workspace only"],
        "read_scope": ["task workspace only"],
        "ports": [],
        "data_boundary": "no external data",
        "credential_policy": "no credentials",
        "merge_owner": "local user",
        "verification_artifacts": [
            "RUN_LEDGER.json",
            "dashboard.html",
            "USAGE_SNAPSHOT.json",
            "adapter-smoke-result.json",
        ],
    }


def smoke_checklist(agent: str) -> str:
    return "\n".join(
        [
            f"# {agent} Adapter Smoke Checklist",
            "",
            "This checklist must pass before the adapter can move from disabled to supervised.",
            "",
            "## Required Gates",
            "",
            "- [ ] Capability manifest validates with `mco schema validate adapter-manifest`.",
            "- [ ] Sandbox contract validates with `mco schema validate sandbox-contract`.",
            "- [ ] Adapter doctor proves binary discovery and authentication without exposing credentials.",
            "- [ ] Non-interactive command contract is documented and deterministic.",
            "- [ ] Execution report captures command shape, timeout, stdout/stderr, success, and failure reason.",
            "- [ ] Usage snapshot reports known costs or explicitly preserves `unknown` quota state.",
            "- [ ] Smoke command is explicit opt-in and budget/timeout capped.",
            "- [ ] Smoke command writes task-local evidence only.",
            "- [ ] CI uses fake adapter fixtures; real provider calls are never implicit.",
            "",
            "## Promotion Rule",
            "",
            "Do not mark the adapter supervised until every gate above has durable evidence.",
            "",
        ]
    )


def onboarding_readme(agent: str) -> str:
    return "\n".join(
        [
            f"# {agent} Adapter Kit",
            "",
            "This kit starts disabled by design. Do not wire it into execution until every gate has evidence.",
            "",
            "## Files",
            "",
            f"- `{agent}.adapter.json` — disabled capability manifest.",
            f"- `{agent}.sandbox.json` — draft sandbox contract.",
            f"- `{agent}-smoke-checklist.md` — promotion gate checklist.",
            f"- `fake-{agent}.py` — deterministic fake CLI fixture for tests.",
            f"- `test_{agent.replace('-', '_')}_adapter_contract.py` — unittest skeleton for local contract checks.",
            "",
            "## Suggested Path",
            "",
            "1. Validate the manifest and sandbox.",
            "2. Prove a fake CLI contract in tests.",
            "3. Implement capability discovery and doctor checks.",
            "4. Implement bounded non-interactive execution.",
            "5. Add execution report and usage snapshot evidence.",
            "6. Add an explicit opt-in smoke command for the real CLI.",
            "7. Only then promote the adapter from disabled to supervised.",
            "",
            "## Validation",
            "",
            "```bash",
            f"mco schema validate adapter-manifest {agent}.adapter.json",
            f"mco schema validate sandbox-contract {agent}.sandbox.json",
            f"python -m unittest test_{agent.replace('-', '_')}_adapter_contract.py",
            "```",
            "",
        ]
    )


def fake_cli_fixture(agent: str) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env python3",
            "from __future__ import annotations",
            "",
            "import sys",
            "",
            "args = sys.argv[1:]",
            "if args == ['--version']:",
            f"    print('{agent} fake 0.1.0')",
            "    raise SystemExit(0)",
            "if args == ['--help']:",
            "    print('--prompt <prompt> --output-format text')",
            "    raise SystemExit(0)",
            "if '--prompt' in args:",
            "    print('MCO_ADAPTER_SMOKE_OK')",
            "    raise SystemExit(0)",
            "print('unexpected args', args)",
            "raise SystemExit(2)",
            "",
        ]
    )


def contract_test_template(agent: str) -> str:
    module_name = agent.replace("-", "_")
    return "\n".join(
        [
            "from __future__ import annotations",
            "",
            "import json",
            "import subprocess",
            "import sys",
            "import unittest",
            "from pathlib import Path",
            "",
            "",
            f"AGENT = {agent!r}",
            f"ROOT = Path(__file__).resolve().parent",
            "",
            "",
            f"class {''.join(part.title() for part in module_name.split('_'))}AdapterContractTests(unittest.TestCase):",
            "    def test_manifest_starts_disabled(self) -> None:",
            "        payload = json.loads((ROOT / f'{AGENT}.adapter.json').read_text(encoding='utf-8'))",
            "        self.assertEqual(payload['agent'], AGENT)",
            "        self.assertFalse(payload['supervised'])",
            "        self.assertFalse(payload['non_interactive'])",
            "        self.assertEqual(payload['quota_status'], 'unknown')",
            "",
            "    def test_fake_cli_fixture_is_deterministic(self) -> None:",
            "        fixture = ROOT / f'fake-{AGENT}.py'",
            "        version = subprocess.run([sys.executable, str(fixture), '--version'], text=True, capture_output=True, check=False)",
            "        self.assertEqual(version.returncode, 0, version.stderr)",
            "        prompt = subprocess.run([sys.executable, str(fixture), '--prompt', 'hello'], text=True, capture_output=True, check=False)",
            "        self.assertEqual(prompt.returncode, 0, prompt.stderr)",
            "        self.assertIn('MCO_ADAPTER_SMOKE_OK', prompt.stdout)",
            "",
            "",
            "if __name__ == '__main__':",
            "    unittest.main()",
            "",
        ]
    )


def scaffold_adapter(agent: str, output_dir: Path, force: bool = False) -> dict:
    validate_agent_name(agent)
    output_dir.mkdir(parents=True, exist_ok=True)
    test_name = f"test_{agent.replace('-', '_')}_adapter_contract.py"
    files = {
        f"{agent}.adapter.json": json.dumps(disabled_manifest(agent), indent=2) + "\n",
        f"{agent}.sandbox.json": json.dumps(sandbox_draft(agent), indent=2) + "\n",
        f"{agent}-smoke-checklist.md": smoke_checklist(agent),
        "README.md": onboarding_readme(agent),
        f"fake-{agent}.py": fake_cli_fixture(agent),
        test_name: contract_test_template(agent),
    }
    written = []
    for name, content in files.items():
        path = output_dir / name
        if path.exists() and not force:
            raise FileExistsError(f"refusing to overwrite existing file: {path}")
        path.write_text(content, encoding="utf-8")
        if name.startswith("fake-") and name.endswith(".py"):
            path.chmod(0o755)
        written.append(str(path))
    return {
        "schema": "mco.adapter_scaffold.v1.0",
        "agent": agent,
        "output_dir": str(output_dir),
        "files": written,
        "status": "created",
    }
