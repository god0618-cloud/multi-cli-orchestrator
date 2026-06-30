from __future__ import annotations

import json
import os
import subprocess
import sys
import hashlib
from pathlib import Path

from mco.adapters.claude import claude_code_binary
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


def _ensure_path_within(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path must be inside task workspace: {path}") from exc
    return resolved


def _claude_env(binary: str) -> dict[str, str]:
    env = {
        "PATH": os.pathsep.join([str(Path(binary).parent), "/usr/bin", "/bin", "/opt/homebrew/bin"]),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
        "TERM": os.environ.get("TERM", "dumb"),
    }
    return {key: value for key, value in env.items() if value}


def _claude_succeeded(exit_code: int | None, stdout: str) -> tuple[bool, str]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        if exit_code != 0:
            return False, f"claude exited with code {exit_code}"
        return True, "claude completed with non-json output"
    if payload.get("is_error") is True:
        return False, f"claude reported error subtype={payload.get('subtype', 'unknown')}"
    subtype = str(payload.get("subtype", ""))
    if subtype.startswith("error"):
        return False, f"claude reported error subtype={subtype}"
    if exit_code != 0:
        return False, f"claude exited with code {exit_code}"
    return True, "claude completed"


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


def execute_dispatch_claude_prompt(
    task_dir: Path,
    dispatch_id: str,
    agent: str,
    sandbox_path: Path | None,
    prompt_file: Path,
    timeout_seconds: int = 120,
    max_output_bytes: int = 80_000,
    max_budget_usd: float = 0.25,
) -> dict:
    if agent != "claude-code":
        raise ValueError("claude prompt execution requires agent=claude-code")
    if sandbox_path is None:
        reason = "sandbox contract is required before dispatch execution"
        block_dispatch(task_dir, dispatch_id, agent, reason)
        raise ValueError(reason)
    if timeout_seconds < 5 or timeout_seconds > 600:
        raise ValueError("timeout_seconds must be between 5 and 600")
    if max_output_bytes < 1000 or max_output_bytes > 500_000:
        raise ValueError("max_output_bytes must be between 1000 and 500000")
    if max_budget_usd <= 0 or max_budget_usd > 1:
        raise ValueError("max_budget_usd must be > 0 and <= 1")

    sandbox = enforce_sandbox(agent, sandbox_path)
    add_sandbox_contract_ref(task_dir, sandbox_path)
    _ensure_claimed(task_dir, dispatch_id, agent)

    prompt_path = _ensure_path_within(prompt_file, task_dir)
    prompt = prompt_path.read_text(encoding="utf-8")
    if len(prompt.encode("utf-8")) > 50_000:
        raise ValueError("prompt_file exceeds 50000 bytes")

    binary = claude_code_binary()
    if not binary:
        reason = "claude binary not found"
        fail_dispatch(task_dir, dispatch_id, agent, reason)
        raise ValueError(reason)

    command = [
        binary,
        "--print",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--permission-mode",
        "default",
        "--tools",
        "",
        "--max-budget-usd",
        f"{max_budget_usd:.4f}",
        "--append-system-prompt",
        "You are running inside Multi CLI Orchestrator supervised adapter mode. Do not ask for additional permissions. Do not claim to have edited files. Return concise task output only.",
        prompt,
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=task_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env=_claude_env(binary),
        )
        stdout, stdout_truncated = _truncate(completed.stdout, max_output_bytes)
        stderr, stderr_truncated = _truncate(completed.stderr, max_output_bytes)
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _truncate(exc.stdout or "", max_output_bytes)
        stderr = f"timeout after {timeout_seconds}s"
        stderr_truncated = False
        exit_code = None

    ok, summary = _claude_succeeded(exit_code, stdout)
    report = {
        "schema": "mco.claude_execution_report.v1.0",
        "dispatch_id": dispatch_id,
        "agent": agent,
        "sandbox_worker": sandbox["worker_id"],
        "adapter_binary": binary,
        "prompt_file": str(prompt_path),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "cwd": str(task_dir),
        "timeout_seconds": timeout_seconds,
        "max_output_bytes": max_output_bytes,
        "max_budget_usd": max_budget_usd,
        "exit_code": exit_code,
        "success": ok,
        "summary": summary,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "command_shape": "claude --print --output-format json --no-session-persistence --permission-mode default --tools '' --max-budget-usd <amount> <prompt>",
    }

    artifact_path = task_dir / "artifacts" / f"{dispatch_id}-claude-execution-report.json"
    artifact_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    register_artifact(task_dir, artifact_path, f"{dispatch_id}-claude-execution-report")
    append_event(
        task_dir,
        "adapter_execution",
        f"Claude Code supervised execution for {agent}: {summary}",
        {"dispatch_id": dispatch_id, "artifact": str(artifact_path), "success": ok, "exit_code": exit_code},
    )
    if ok:
        return complete_dispatch(task_dir, dispatch_id, agent, "Claude Code supervised prompt execution completed.")
    fail_dispatch(task_dir, dispatch_id, agent, summary)
    raise ValueError(summary)
