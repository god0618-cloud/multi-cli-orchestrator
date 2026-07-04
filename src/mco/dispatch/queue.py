from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mco.adapters.gate import evaluate_adapter_gate
from mco.replay.ledger import append_event


def dispatch_root(task_dir: Path) -> Path:
    return task_dir / "dispatch"


def inbox_dir(task_dir: Path, agent: str) -> Path:
    return dispatch_root(task_dir) / "agent-inbox" / agent


def dispatch_path(task_dir: Path, dispatch_id: str) -> Path:
    return dispatch_root(task_dir) / "dispatches" / f"{dispatch_id}.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_time(value: object) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def queue_dispatch(
    task_dir: Path,
    agent: str,
    title: str,
    instructions: str,
    require_ready: bool = False,
    sandbox_path: Path | None = None,
    max_attempts: int = 3,
) -> dict:
    if max_attempts < 1 or max_attempts > 10:
        raise ValueError("max_attempts must be between 1 and 10")
    root = dispatch_root(task_dir)
    (root / "dispatches").mkdir(parents=True, exist_ok=True)
    now = _utc_now()
    dispatch_id = now.strftime("%Y%m%d-%H%M%S-%f") + f"-{agent}"
    gate = evaluate_adapter_gate(agent, sandbox_path) if require_ready else None
    status = "queued" if gate is None or gate.allowed else "blocked"
    payload = {
        "schema": "mco.dispatch.v0.5",
        "dispatch_id": dispatch_id,
        "agent": agent,
        "title": title,
        "instructions": instructions,
        "status": status,
        "created_at": _iso(now),
        "claimed_at": None,
        "completed_at": _iso(now) if status == "blocked" else None,
        "completion": {"error": gate.reason, "gate": gate.to_dict()} if gate is not None and not gate.allowed else None,
        "gate": gate.to_dict() if gate is not None else None,
        "attempt": 0,
        "max_attempts": max_attempts,
        "lease_expires_at": None,
        "last_heartbeat_at": None,
        "reclaim_count": 0,
        "last_reclaimed_at": None,
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


def claim_dispatch(task_dir: Path, dispatch_id: str, agent: str, lease_seconds: int = 900) -> dict:
    if lease_seconds < 30 or lease_seconds > 86400:
        raise ValueError("lease_seconds must be between 30 and 86400")
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] != "queued":
        raise ValueError(f"dispatch {dispatch_id} is not queued: {payload['status']}")
    attempt = int(payload.get("attempt") or 0) + 1
    max_attempts = int(payload.get("max_attempts") or 3)
    if attempt > max_attempts:
        payload["status"] = "blocked"
        payload["completed_at"] = _iso(_utc_now())
        payload["completion"] = {"error": f"max attempts exhausted before claim: {max_attempts}"}
        write_dispatch(task_dir, payload)
        append_event(task_dir, "dispatch_attempts_exhausted", f"Dispatch exhausted max attempts before claim by {agent}", {"dispatch_id": dispatch_id, "attempt": attempt, "max_attempts": max_attempts})
        return payload
    now = _utc_now()
    payload["status"] = "claimed"
    payload["claimed_at"] = _iso(now)
    payload["attempt"] = attempt
    payload["max_attempts"] = max_attempts
    payload["lease_expires_at"] = _iso(now + timedelta(seconds=lease_seconds))
    payload["last_heartbeat_at"] = _iso(now)
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_claimed", f"Dispatch claimed by {agent}", {"dispatch_id": dispatch_id, "attempt": attempt, "lease_expires_at": payload["lease_expires_at"]})
    append_event(task_dir, "dispatch_lease_acquired", f"Lease acquired by {agent}", {"dispatch_id": dispatch_id, "attempt": attempt, "lease_seconds": lease_seconds})
    return payload


def heartbeat_dispatch(task_dir: Path, dispatch_id: str, agent: str, lease_seconds: int = 900) -> dict:
    if lease_seconds < 30 or lease_seconds > 86400:
        raise ValueError("lease_seconds must be between 30 and 86400")
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] != "claimed":
        raise ValueError(f"dispatch {dispatch_id} is not claimed: {payload['status']}")
    now = _utc_now()
    payload["last_heartbeat_at"] = _iso(now)
    payload["lease_expires_at"] = _iso(now + timedelta(seconds=lease_seconds))
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_heartbeat", f"Heartbeat received from {agent}", {"dispatch_id": dispatch_id, "attempt": payload.get("attempt", 0), "lease_expires_at": payload["lease_expires_at"]})
    return payload


def reclaim_stale_dispatches(task_dir: Path, now: datetime | None = None, limit: int = 100) -> dict:
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")
    current = (now or _utc_now()).astimezone(timezone.utc)
    reclaimed: list[dict] = []
    exhausted: list[dict] = []
    inspected = 0
    for payload in list_dispatches(task_dir):
        if inspected >= limit:
            break
        inspected += 1
        if payload.get("status") != "claimed":
            continue
        lease_expires_at = _parse_time(payload.get("lease_expires_at"))
        if lease_expires_at is None or lease_expires_at > current:
            continue

        attempt = int(payload.get("attempt") or 0)
        max_attempts = int(payload.get("max_attempts") or 3)
        if attempt >= max_attempts:
            payload["status"] = "blocked"
            payload["completed_at"] = _iso(current)
            payload["completion"] = {"error": f"max attempts exhausted after stale lease: {attempt}/{max_attempts}"}
            write_dispatch(task_dir, payload)
            exhausted.append({"dispatch_id": payload["dispatch_id"], "agent": payload.get("agent"), "attempt": attempt, "max_attempts": max_attempts})
            append_event(task_dir, "dispatch_attempts_exhausted", f"Dispatch blocked after stale lease exhausted attempts: {payload['dispatch_id']}", {"dispatch_id": payload["dispatch_id"], "attempt": attempt, "max_attempts": max_attempts})
            continue

        payload["status"] = "queued"
        payload["claimed_at"] = None
        payload["lease_expires_at"] = None
        payload["last_reclaimed_at"] = _iso(current)
        payload["reclaim_count"] = int(payload.get("reclaim_count") or 0) + 1
        payload["completion"] = None
        write_dispatch(task_dir, payload)
        reclaimed.append({"dispatch_id": payload["dispatch_id"], "agent": payload.get("agent"), "attempt": attempt, "max_attempts": max_attempts})
        append_event(task_dir, "dispatch_reclaimed", f"Stale dispatch returned to queue: {payload['dispatch_id']}", {"dispatch_id": payload["dispatch_id"], "attempt": attempt, "max_attempts": max_attempts, "lease_expired_at": _iso(lease_expires_at)})

    return {
        "schema": "mco.dispatch_reclaim.v1.0",
        "inspected": inspected,
        "reclaimed": reclaimed,
        "exhausted": exhausted,
        "reclaimed_count": len(reclaimed),
        "exhausted_count": len(exhausted),
    }


def complete_dispatch(task_dir: Path, dispatch_id: str, agent: str, summary: str) -> dict:
    payload = read_dispatch(task_dir, dispatch_id)
    if payload["agent"] != agent:
        raise ValueError(f"dispatch {dispatch_id} is assigned to {payload['agent']}, not {agent}")
    if payload["status"] not in {"queued", "claimed"}:
        raise ValueError(f"dispatch {dispatch_id} cannot be completed from status: {payload['status']}")
    payload["status"] = "completed"
    payload["completed_at"] = _iso(_utc_now())
    payload["lease_expires_at"] = None
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
    payload["completed_at"] = _iso(_utc_now())
    payload["lease_expires_at"] = None
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
    payload["completed_at"] = _iso(_utc_now())
    payload["lease_expires_at"] = None
    payload["completion"] = {"error": reason}
    write_dispatch(task_dir, payload)
    append_event(task_dir, "dispatch_failed", f"Dispatch failed for {agent}: {reason}", {"dispatch_id": dispatch_id})
    return payload
