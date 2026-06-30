from __future__ import annotations

import json
import os
import shutil
import subprocess


REQUIRED_HELP_FLAGS = [
    "--print",
    "--output-format",
    "--max-budget-usd",
    "--no-session-persistence",
    "--permission-mode",
    "--tools",
]


def claude_code_binary() -> str | None:
    override = os.environ.get("CLAUDE_CODE_BIN")
    if override:
        return override
    return shutil.which("claude")


def claude_code_manifest() -> dict:
    return {
        "schema": "mco.adapter_manifest.v1.2",
        "agent": "claude-code",
        "adapter_type": "first-party-supervised",
        "interactive": True,
        "non_interactive": True,
        "supervised": True,
        "can_read_inbox": True,
        "can_write_artifacts": True,
        "can_run_shell": False,
        "can_use_browser": False,
        "quota_status": "budget_limited",
        "safe_command_allowlist": [
            "claude --print --output-format json --no-session-persistence --permission-mode default --tools '' --max-budget-usd <amount> <prompt>"
        ],
    }


def probe_claude_code() -> list[dict]:
    checks: list[dict] = []
    binary = claude_code_binary()
    if not binary:
        return [{"name": "binary", "status": "FAIL", "detail": "claude not found on PATH and CLAUDE_CODE_BIN not set"}]

    checks.append({"name": "binary", "status": "PASS", "detail": binary})

    version = subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=15, check=False)
    if version.returncode == 0:
        checks.append({"name": "version", "status": "PASS", "detail": version.stdout.strip() or version.stderr.strip()})
    else:
        checks.append({"name": "version", "status": "FAIL", "detail": version.stderr.strip() or version.stdout.strip()})

    help_result = subprocess.run([binary, "--help"], text=True, capture_output=True, timeout=15, check=False)
    help_text = help_result.stdout + help_result.stderr
    if help_result.returncode != 0:
        checks.append({"name": "help", "status": "FAIL", "detail": help_text.strip()})
    else:
        missing = [flag for flag in REQUIRED_HELP_FLAGS if flag not in help_text]
        if missing:
            checks.append({"name": "non_interactive_flags", "status": "FAIL", "detail": ", ".join(missing)})
        else:
            checks.append({"name": "non_interactive_flags", "status": "PASS", "detail": ", ".join(REQUIRED_HELP_FLAGS)})

    auth = subprocess.run([binary, "auth", "status"], text=True, capture_output=True, timeout=15, check=False)
    auth_text = auth.stdout.strip() or auth.stderr.strip()
    if auth.returncode != 0:
        checks.append({"name": "auth_status", "status": "FAIL", "detail": auth_text})
    else:
        try:
            payload = json.loads(auth.stdout)
            logged_in = payload.get("loggedIn") is True
            checks.append(
                {
                    "name": "auth_status",
                    "status": "PASS" if logged_in else "FAIL",
                    "detail": {
                        "loggedIn": payload.get("loggedIn"),
                        "authMethod": payload.get("authMethod"),
                        "apiProvider": payload.get("apiProvider"),
                    },
                }
            )
        except json.JSONDecodeError:
            checks.append({"name": "auth_status", "status": "PASS", "detail": auth_text})

    return checks
