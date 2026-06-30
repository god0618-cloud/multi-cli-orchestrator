from __future__ import annotations


def generic_cli_manifest() -> dict:
    return {
        "schema": "mco.adapter_manifest.v1.0",
        "agent": "generic-cli",
        "adapter_type": "generic",
        "interactive": False,
        "non_interactive": True,
        "supervised": True,
        "can_read_inbox": True,
        "can_write_artifacts": True,
        "can_run_shell": True,
        "can_use_browser": False,
        "quota_status": "not_applicable",
        "safe_command_allowlist": ["echo", "python -c print-only"],
    }
