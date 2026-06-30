from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mco.dispatch.queue import block_dispatch, claim_dispatch, complete_dispatch, fail_dispatch, read_dispatch
from mco.replay.ledger import add_sandbox_contract_ref, append_event, register_artifact
from mco.sandbox.enforcer import enforce_sandbox


DISALLOWED_PYTHON_TOKENS = [
    "import",
    "open",
    "exec",
    "eval",
    "compile",
    "__",
    "os.",
    "sys.",
    "subprocess",
    "pathlib",
    "shutil",
    "socket",
    "write",
]


def _ensure_claimed(task_dir: Path, dispatch_id: str, agent: str) -> dict:
    dispatch = read_dispatch(task_dir, dispatch_id)
    if dispatch["status"] == "queued":
        return claim_dispatch(task_dir, dispatch_id, agent)
    if dispatch["status"] != "claimed":
        raise ValueError(f"dispatch cannot execute from status: {dispatch['status']}")
    return dispatch


def _truncate(text: str, max_bytes: int) -> tuple[str, bool]:
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text, False
    truncated = data[:max_bytes].decode("utf-8", errors="replace")
    return truncated, True


def validate_safe_command(command: list[str]) -> None:
    if not command:
        raise ValueError("command cannot be empty")
    if command[0] == "echo":
        return
    if len(command) == 3 and command[0] == "python" and command[1] == "-c":
        code = command[2]
        stripped = code.strip()
        if not stripped.startswith("print("):
            raise ValueError("python -c is restricted to print(...)")
        lowered = stripped.lower()
        for token in DISALLOWED_PYTHON_TOKENS:
            if token in lowered:
                raise ValueError(f"python -c contains disallowed token: {token}")
        return
    raise ValueError("command is not in safe allowlist")


def resolve_safe_command(command: list[str]) -> list[str]:
    if len(command) == 3 and command[0] == "python" and command[1] == "-c":
        return [sys.executable, "-c", command[2]]
    return command


def execute_dispatch_dry_run(task_dir: Path, dispatch_id: str, agent: str, sandbox_path: Path | None) -> dict:
    if sandbox_path is None:
        reason = "sandbox contract is required before dispatch execution"
        block_dispatch(task_dir, dispatch_id, agent, reason)
        raise ValueError(reason)

    sandbox = enforce_sandbox(agent, sandbox_path)
    add_sandbox_contract_ref(task_dir, sandbox_path)
    dispatch = _ensure_claimed(task_dir, dispatch_id, agent)

    artifact_path = task_dir / "artifacts" / f"{dispatch_id}-dry-run.md"
    artifact_path.write_text(
        "\n".join(
            [
                "# Dispatch Dry Run Evidence",
                "",
                f"Dispatch: `{dispatch_id}`",
                f"Agent: `{agent}`",
                f"Sandbox worker: `{sandbox['worker_id']}`",
                "",
                "No external CLI command was executed. v1.0 validates capability and sandbox gates only in dry-run mode.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    register_artifact(task_dir, artifact_path, f"{dispatch_id}-dry-run")
    append_event(
        task_dir,
        "adapter_execution_dry_run",
        f"Dry-run execution passed for {agent}",
        {"dispatch_id": dispatch_id, "sandbox": str(sandbox_path.resolve())},
    )
    return complete_dispatch(task_dir, dispatch_id, agent, "Dry-run execution passed capability and sandbox gates.")


def execute_dispatch_command(
    task_dir: Path,
    dispatch_id: str,
    agent: str,
    sandbox_path: Path | None,
    command: list[str],
    timeout_seconds: int = 10,
    max_output_bytes: int = 20_000,
) -> dict:
    if sandbox_path is None:
        reason = "sandbox contract is required before dispatch execution"
        block_dispatch(task_dir, dispatch_id, agent, reason)
        raise ValueError(reason)
    if timeout_seconds < 1 or timeout_seconds > 60:
        raise ValueError("timeout_seconds must be between 1 and 60")
    if max_output_bytes < 100 or max_output_bytes > 200_000:
        raise ValueError("max_output_bytes must be between 100 and 200000")

    sandbox = enforce_sandbox(agent, sandbox_path)
    add_sandbox_contract_ref(task_dir, sandbox_path)
    validate_safe_command(command)
    _ensure_claimed(task_dir, dispatch_id, agent)

    try:
        completed = subprocess.run(
            resolve_safe_command(command),
            cwd=task_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env={"PATH": "/usr/bin:/bin:/opt/homebrew/bin"},
        )
        stdout, stdout_truncated = _truncate(completed.stdout, max_output_bytes)
        stderr, stderr_truncated = _truncate(completed.stderr, max_output_bytes)
        report = {
            "schema": "mco.execution_report.v1.0",
            "dispatch_id": dispatch_id,
            "agent": agent,
            "sandbox_worker": sandbox["worker_id"],
            "command": command,
            "cwd": str(task_dir),
            "timeout_seconds": timeout_seconds,
            "max_output_bytes": max_output_bytes,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
        }
    except subprocess.TimeoutExpired as exc:
        report = {
            "schema": "mco.execution_report.v1.0",
            "dispatch_id": dispatch_id,
            "agent": agent,
            "sandbox_worker": sandbox["worker_id"],
            "command": command,
            "cwd": str(task_dir),
            "timeout_seconds": timeout_seconds,
            "max_output_bytes": max_output_bytes,
            "exit_code": None,
            "stdout": _truncate(exc.stdout or "", max_output_bytes)[0],
            "stderr": f"timeout after {timeout_seconds}s",
            "stdout_truncated": False,
            "stderr_truncated": False,
        }

    artifact_path = task_dir / "artifacts" / f"{dispatch_id}-execution-report.json"
    artifact_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    register_artifact(task_dir, artifact_path, f"{dispatch_id}-execution-report")
    append_event(
        task_dir,
        "adapter_execution",
        f"Adapter command executed for {agent}: exit_code={report['exit_code']}",
        {"dispatch_id": dispatch_id, "artifact": str(artifact_path), "exit_code": report["exit_code"]},
    )
    if report["exit_code"] == 0:
        return complete_dispatch(task_dir, dispatch_id, agent, "Safe command execution completed.")
    fail_dispatch(task_dir, dispatch_id, agent, f"safe command failed with exit code {report['exit_code']}")
    raise ValueError(f"safe command failed with exit code {report['exit_code']}")
