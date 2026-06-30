from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mco.adapters.doctor import doctor_adapter
from mco.config import WorkspaceConfig
from mco.dashboard.static import render_dashboard
from mco.dispatch.execute import execute_dispatch_claude_prompt
from mco.dispatch.queue import queue_dispatch
from mco.task.lifecycle import create_task
from mco.usage.snapshot import write_usage_snapshot


SMOKE_SENTINEL = "MCO_ADAPTER_SMOKE_OK"


def _default_claude_sandbox_template() -> Path:
    source_tree = Path(__file__).resolve().parents[3] / "templates" / "sandbox-contracts" / "claude-code-supervised.json"
    if source_tree.exists():
        return source_tree
    packaged = Path(__file__).resolve().parents[1] / "templates" / "sandbox-contracts" / "claude-code-supervised.json"
    if packaged.exists():
        return packaged
    raise FileNotFoundError("claude-code supervised sandbox template not found")


def smoke_claude_code(
    config: WorkspaceConfig,
    max_budget_usd: float = 0.05,
    timeout_seconds: int = 120,
    max_output_bytes: int = 80_000,
) -> dict[str, Any]:
    if max_budget_usd <= 0 or max_budget_usd > 0.25:
        raise ValueError("smoke max_budget_usd must be > 0 and <= 0.25")

    created = create_task(
        config,
        "Claude Code Adapter Smoke",
        "Run a bounded non-interactive Claude Code adapter smoke test.",
    )
    sandbox_path = created.task_dir / "SANDBOX_CONTRACT.json"
    sandbox_path.write_text(_default_claude_sandbox_template().read_text(encoding="utf-8"), encoding="utf-8")

    doctor = doctor_adapter("claude-code", sandbox_path)
    if doctor.status != "READY_SUPERVISED":
        result = {
            "schema": "mco.adapter_smoke.v1.0",
            "agent": "claude-code",
            "status": "BLOCKED",
            "task_id": created.task_id,
            "task_dir": str(created.task_dir),
            "doctor": doctor.to_dict(),
        }
        out = created.task_dir / "adapter-smoke-result.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    dispatch = queue_dispatch(
        created.task_dir,
        "claude-code",
        "Claude Code smoke prompt",
        f"Return exactly {SMOKE_SENTINEL}.",
    )
    prompt = created.task_dir / "prompt.md"
    prompt.write_text(f"Return exactly this string and nothing else: {SMOKE_SENTINEL}\n", encoding="utf-8")

    status = "PASS"
    error = None
    try:
        execute_dispatch_claude_prompt(
            created.task_dir,
            dispatch["dispatch_id"],
            "claude-code",
            sandbox_path,
            prompt,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
            max_budget_usd=max_budget_usd,
        )
    except Exception as exc:
        status = "FAIL"
        error = str(exc)

    usage_snapshot = write_usage_snapshot(created.task_dir)
    dashboard = render_dashboard(config, created.task_id)
    report_path = created.task_dir / "artifacts" / f"{dispatch['dispatch_id']}-claude-execution-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}

    if status == "PASS" and SMOKE_SENTINEL not in str(report.get("stdout", "")):
        status = "FAIL"
        error = "smoke sentinel missing from Claude stdout"

    result = {
        "schema": "mco.adapter_smoke.v1.0",
        "agent": "claude-code",
        "status": status,
        "task_id": created.task_id,
        "task_dir": str(created.task_dir),
        "dispatch_id": dispatch["dispatch_id"],
        "doctor": doctor.to_dict(),
        "execution_report": str(report_path) if report_path.exists() else None,
        "usage_snapshot": str(usage_snapshot),
        "dashboard": str(dashboard),
        "max_budget_usd": max_budget_usd,
        "sentinel": SMOKE_SENTINEL,
        "error": error,
    }
    out = created.task_dir / "adapter-smoke-result.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
