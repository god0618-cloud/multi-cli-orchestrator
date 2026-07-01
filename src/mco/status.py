from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mco.adapters.matrix import build_adapter_matrix
from mco.audit.safety import audit_tree
from mco.config import WorkspaceConfig
from mco.dispatch.queue import list_dispatches
from mco.task.lifecycle import list_tasks, task_dir


DISPATCH_STATES = ["queued", "claimed", "completed", "blocked", "failed"]


@dataclass(frozen=True)
class StatusSnapshot:
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.payload, indent=2)


def _select_task(config: WorkspaceConfig, task_id: str | None) -> dict[str, Any] | None:
    tasks = list_tasks(config)
    if not tasks:
        return None
    if task_id:
        for task in tasks:
            if task.get("task_id") == task_id:
                return task
        raise FileNotFoundError(f"task not found: {task_id}")
    return sorted(tasks, key=lambda item: str(item.get("created_at", "")))[-1]


def _dispatch_summary(config: WorkspaceConfig, task: dict[str, Any] | None) -> dict[str, Any]:
    counts = {state: 0 for state in DISPATCH_STATES}
    latest: dict[str, Any] | None = None
    if task is None:
        return {"counts": counts, "latest": None}

    dispatches = list_dispatches(task_dir(config, str(task["task_id"])))
    for dispatch in dispatches:
        status = str(dispatch.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    if dispatches:
        latest = sorted(dispatches, key=lambda item: str(item.get("created_at", "")))[-1]
        latest = {
            "dispatch_id": latest.get("dispatch_id"),
            "agent": latest.get("agent"),
            "title": latest.get("title"),
            "status": latest.get("status"),
        }
    return {"counts": counts, "latest": latest}


def _adapter_summary() -> list[dict[str, Any]]:
    matrix = build_adapter_matrix(include_doctor=False)
    rows = []
    for row in matrix["agents"]:
        readiness = str(row.get("readiness", "UNKNOWN"))
        rows.append(
            {
                "agent": row.get("agent"),
                "readiness": readiness,
                "quota_status": row.get("quota_status"),
                "gate": "auto-dispatch-ok" if readiness == "READY_SUPERVISED" else "requires-review",
                "promotion_blockers": row.get("promotion_blockers", []),
            }
        )
    return rows


def build_status_snapshot(config: WorkspaceConfig, task_id: str | None = None, include_audit: bool = False) -> StatusSnapshot:
    task = _select_task(config, task_id)
    audit_payload: dict[str, Any] | None = None
    if include_audit:
        audit = audit_tree(config.workspace_root)
        audit_payload = {
            "pass": audit.pass_count,
            "warn": audit.warn_count,
            "fail": audit.fail_count,
            "ok": audit.ok,
        }

    payload = {
        "schema": "mco.status.v1.0",
        "workspace": str(config.workspace_root),
        "task": None
        if task is None
        else {
            "task_id": task.get("task_id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "created_at": task.get("created_at"),
            "artifacts_dir": task.get("artifacts_dir"),
        },
        "dispatch": _dispatch_summary(config, task),
        "adapters": _adapter_summary(),
        "audit": audit_payload,
    }
    return StatusSnapshot(payload)


def render_status_text(snapshot: StatusSnapshot) -> str:
    payload = snapshot.payload
    lines = [
        "MCO Status",
        f"workspace: {payload['workspace']}",
    ]
    task = payload.get("task")
    if task is None:
        lines.append("task: none")
    else:
        lines.append(f"task: {task['task_id']} | {task['status']} | {task['title']}")

    dispatch = payload["dispatch"]
    counts = dispatch["counts"]
    lines.append(
        "dispatch: "
        + " ".join(f"{state}={counts.get(state, 0)}" for state in DISPATCH_STATES)
    )
    if dispatch.get("latest"):
        latest = dispatch["latest"]
        lines.append(f"latest_dispatch: {latest['dispatch_id']} | {latest['agent']} | {latest['status']} | {latest['title']}")

    lines.append("adapters:")
    for row in payload["adapters"]:
        lines.append(f"  - {row['agent']}: {row['readiness']} | quota={row['quota_status']} | gate={row['gate']}")

    audit = payload.get("audit")
    if audit is not None:
        lines.append(f"audit: PASS={audit['pass']} WARN={audit['warn']} FAIL={audit['fail']}")

    return "\n".join(lines)
