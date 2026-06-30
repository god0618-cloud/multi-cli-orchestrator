from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.dispatch.queue import list_dispatches
from mco.replay.ledger import append_event, read_ledger, register_artifact


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _artifact_path(item: Any) -> Path | None:
    if isinstance(item, dict) and item.get("path"):
        return Path(str(item["path"]))
    return None


def _parse_stdout_cost(report: dict[str, Any]) -> float | None:
    stdout = str(report.get("stdout", "")).strip()
    if not stdout:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    value = payload.get("total_cost_usd")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _agent_record(agent: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "quota_status": "unknown",
        "dispatch_count": 0,
        "completed_dispatch_count": 0,
        "failed_dispatch_count": 0,
        "blocked_dispatch_count": 0,
        "execution_report_count": 0,
        "observed_cost_usd_total": 0.0,
        "max_budget_usd_total": 0.0,
        "budget_remaining_usd_estimate": None,
        "last_error": None,
    }


def build_usage_snapshot(task_dir: Path) -> dict[str, Any]:
    task = _read_json(task_dir / "task.json")
    ledger = read_ledger(task_dir / "RUN_LEDGER.json")
    agents: dict[str, dict[str, Any]] = {}

    for dispatch in list_dispatches(task_dir):
        agent = str(dispatch.get("agent", "unknown"))
        record = agents.setdefault(agent, _agent_record(agent))
        status = str(dispatch.get("status", "unknown"))
        record["dispatch_count"] += 1
        if status == "completed":
            record["completed_dispatch_count"] += 1
        elif status == "failed":
            record["failed_dispatch_count"] += 1
            completion = dispatch.get("completion") or {}
            record["last_error"] = completion.get("error") or completion.get("summary") or "dispatch failed"
        elif status == "blocked":
            record["blocked_dispatch_count"] += 1
            completion = dispatch.get("completion") or {}
            record["last_error"] = completion.get("error") or completion.get("summary") or "dispatch blocked"

    for artifact in ledger.get("artifacts", []):
        path = _artifact_path(artifact)
        if path is None or not path.exists() or path.suffix != ".json":
            continue
        report = _read_json(path)
        agent = report.get("agent")
        if not agent:
            continue
        record = agents.setdefault(str(agent), _agent_record(str(agent)))
        if report.get("schema") in {"mco.claude_execution_report.v1.0", "mco.execution_report.v1.0"}:
            record["execution_report_count"] += 1
        if report.get("schema") == "mco.claude_execution_report.v1.0":
            record["quota_status"] = "budget_limited"
            observed = _parse_stdout_cost(report)
            if observed is not None:
                record["observed_cost_usd_total"] += observed
            budget = report.get("max_budget_usd")
            if isinstance(budget, (int, float)):
                record["max_budget_usd_total"] += float(budget)
            if report.get("success") is False:
                record["quota_status"] = "needs_attention"
                record["last_error"] = report.get("summary") or record["last_error"]

    for record in agents.values():
        if record["max_budget_usd_total"] > 0:
            record["budget_remaining_usd_estimate"] = max(
                record["max_budget_usd_total"] - record["observed_cost_usd_total"],
                0.0,
            )

    return {
        "schema": "mco.usage_snapshot.v1.0",
        "task_id": task.get("task_id", task_dir.name),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "task-local registered artifacts and dispatch records",
        "claims": [
            "observed_cost_usd_total is derived only from execution report stdout JSON when present",
            "budget_remaining_usd_estimate is a local estimate against per-dispatch max_budget_usd, not provider account quota",
            "unknown means no trustworthy task-local usage evidence was available",
        ],
        "agents": sorted(agents.values(), key=lambda item: item["agent"]),
    }


def write_usage_snapshot(task_dir: Path) -> Path:
    snapshot = build_usage_snapshot(task_dir)
    out = task_dir / "USAGE_SNAPSHOT.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    register_artifact(task_dir, out, "usage-snapshot")
    append_event(task_dir, "usage_snapshot", "Usage snapshot generated from task-local evidence.", {"artifact": str(out)})
    return out
