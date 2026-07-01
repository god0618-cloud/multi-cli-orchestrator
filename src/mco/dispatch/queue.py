from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mco.adapters.gate import evaluate_adapter_gate
from mco.replay.ledger import append_event


def dispatch_root(task_dir: Path) -> Path:
    return task_dir / "dispatch"


def inbox_dir(task_dir: Path, agent: str) -> Path:
    return dispatch_root(task_dir) / "agent-inbox" / agent


def dispatch_path(task_dir: Path, dispatch_id: str) -> Path:
    return dispatch_root(task_dir) / "dispatches" / f"{dispatch_id}.json"


def queue_dispatch(
    task_dir: Path,
    agent: str,
    title: str,
    instructions: str,
    require_ready: bool = False,
    sandbox_path: Path | None = None,
) -> dict:
    root = dispatch_root(task_dir)
    (root / "dispatches").mkdir(parents=True, exist_ok=True)
    dispatch_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + f"-{agent}"
    gate = evaluate_adapter_gate(agent, sandbox_path) if require_ready else None
    status = "queued" if gate is None or gate.allowed else "blocked"
    payload = {
        "schema": "mco.dispatch.v0.5",
        "dispatch_id": dispatch_id,
        "agent": agent,
        "title": title,
        "instructions": instructions,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claimed_at": None,
        "completed_at": datetime.now(timezone.utc).isoformat() if status == "blocked" else None,
        "completion": {"error": gate.reason, "gate": gate.to_dict()} if gate is not None and not gate.allowed else None,
        "gate": gate.to_dict() if gate is not None else None,
    }
    dispatch_json = dispatch_path(task_dir, dispatch_id)
    dispatch_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if status == "queued":
        inbox = inbox_dir(task_dir, agent)
        inbox.mkdir(parents=True, exist_ok=True)
        inbox_file = inbox / f"{dispatch_id}.md"
        inbox_file.write_text(
            f"# {title}\n\nDispatch: `{dispatch_id}`\n\nAgent: `{agent}`\n\n## Instructions\n\n{instructions}\n",
            encoding="utf-8",
        )
        append_event(task_dir, "dispatch_queued", f"Dispatch queued for {agent}: {title}", {"dispatch_id": dispatch_id, "gate": payload["gate"]})
    else:
        append_event(task_dir, "dispatch_gate_blocked", f"Dispatch blocked by adapter gate for {agent}: {gate.reason}", {"dispatch_id": dispatch_id, "gate": gate.to_dict()})
    return payload


def read_dispatch(task_dir: Path, dispatch_id: str) -> dict:
    path = dispatch_path(task_dir, dispatch_id)
    if not path.exists():
        raise FileNotFoundError(f"dispatch not found: {dispatch_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_dispatch(task_dir: Path, payload: dict) -> None:
    dispatch_path(task_dir, payload["dispatch_id"]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def list_dispatches(task_dir: Path) -> list[dict]:
    root = dispatch_root(task_dir) / "dispatches"
    if not root.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def claim_dispatch(task_dir: Path, dispatch_id: str, agent: str) -> dict:
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] != "queued":
        raise ValueError(f"dispatch {dispatch_id} is not queued: {payload['status']}")
    payload["status"] = "claimed"
    payload["claimed_at"] = datetime.now(timezone.utc).isoformat()
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_claimed", f"Dispatch claimed by {agent}", {"dispatch_id": dispatch_id})
    return payload


def complete_dispatch(task_dir: Path, dispatch_id: str, agent: str, summary: str) -> dict:
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] not in {"queued", "claimed"}:
        raise ValueError(f"dispatch {dispatch_id} cannot be completed from status: {payload['status']}")
    payload["status"] = "completed"
    payload["completed_at"] = datetime.now(timezone.utc).isoformat()
    payload["completion"] = {"summary": summary}
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_completed", f"Dispatch completed by {agent}: {summary}", {"dispatch_id": dispatch_id})
    return payload


def block_dispatch(task_dir: Path, dispatch_id: str, agent: str, reason: str) -> dict:
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] in {"completed", "blocked"}:
        raise ValueError(f"dispatch {dispatch_id} cannot be blocked from status: {payload['status']}")
    payload["status"] = "blocked"
    payload["completed_at"] = datetime.now(timezone.utc).isoformat()
    payload["completion"] = {"error": reason}
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_blocked", f"Dispatch blocked for {agent}: {reason}", {"dispatch_id": dispatch_id})
    return payload


def fail_dispatch(task_dir: Path, dispatch_id: str, agent: str, reason: str) -> dict:
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] in {"completed", "blocked", "failed"}:
        raise ValueError(f"dispatch {dispatch_id} cannot fail from status: {payload['status']}")
    payload["status"] = "failed"
    payload["completed_at"] = datetime.now(timezone.utc).isoformat()
    payload["completion"] = {"error": reason}
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_failed", f"Dispatch failed for {agent}: {reason}", {"dispatch_id": dispatch_id})
    return payload
