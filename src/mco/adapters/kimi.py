from __future__ import annotations

import os
import shutil
import subprocess


REQUIRED_HELP_FLAGS = [
    "-p, --prompt",
    "--output-format",
]


def kimi_code_binary() -> str | None:
    override = os.environ.get("KIMI_CODE_BIN")
    if override:
        return override
    return shutil.which("kimi")


def kimi_code_manifest() -> dict:
    return {
        "schema": "mco.adapter_manifest.v1.2",
        "agent": "kimi-code",
        "adapter_type": "first-party-supervised",
        "interactive": True,
        "non_interactive": True,
        "supervised": True,
        "can_read_inbox": True,
        "can_write_artifacts": True,
        "can_run_shell": False,
        "can_use_browser": False,
        "quota_status": "unknown",
        "safe_command_allowlist": [
            "kimi --prompt <prompt> --output-format text"
        ],
    }


def probe_kimi_code() -> list[dict]:
    checks: list[dict] = []
    binary = kimi_code_binary()
    if not binary:
        return [{"name": "binary", "status": "FAIL", "detail": "kimi not found on PATH and KIMI_CODE_BIN not set"}]

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

    doctor = subprocess.run([binary, "doctor"], text=True, capture_output=True, timeout=30, check=False)
    doctor_text = (doctor.stdout.strip() or doctor.stderr.strip())[:2000]
    checks.append(
        {
            "name": "doctor",
            "status": "PASS" if doctor.returncode == 0 else "FAIL",
            "detail": doctor_text,
        }
    )
    return checks
