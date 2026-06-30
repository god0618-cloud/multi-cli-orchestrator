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


def scaffold_adapter(agent: str, output_dir: Path, force: bool = False) -> dict:
    validate_agent_name(agent)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        f"{agent}.adapter.json": json.dumps(disabled_manifest(agent), indent=2) + "\n",
        f"{agent}.sandbox.json": json.dumps(sandbox_draft(agent), indent=2) + "\n",
        f"{agent}-smoke-checklist.md": smoke_checklist(agent),
    }
    written = []
    for name, content in files.items():
        path = output_dir / name
        if path.exists() and not force:
            raise FileExistsError(f"refusing to overwrite existing file: {path}")
        path.write_text(content, encoding="utf-8")
        written.append(str(path))
    return {
        "schema": "mco.adapter_scaffold.v1.0",
        "agent": agent,
        "output_dir": str(output_dir),
        "files": written,
        "status": "created",
    }
