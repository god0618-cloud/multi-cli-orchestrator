from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.dispatch.queue import queue_dispatch
from mco.replay.ledger import append_event


MAX_WAVE_WORKERS = 6


def _validate_worker(item: dict[str, Any], index: int) -> dict[str, str | None]:
    if not isinstance(item, dict):
        raise ValueError(f"worker[{index}] must be an object")
    agent = item.get("agent")
    title = item.get("title")
    instructions = item.get("instructions")
    sandbox = item.get("sandbox")
    if not isinstance(agent, str) or not agent:
        raise ValueError(f"worker[{index}].agent is required")
    if not isinstance(title, str) or not title:
        raise ValueError(f"worker[{index}].title is required")
    if not isinstance(instructions, str) or not instructions:
        raise ValueError(f"worker[{index}].instructions is required")
    if sandbox is not None and (not isinstance(sandbox, str) or not sandbox):
        raise ValueError(f"worker[{index}].sandbox must be a path string when provided")
    return {"agent": agent, "title": title, "instructions": instructions, "sandbox": sandbox}


def load_wave_spec(path: Path) -> dict[str, Any]:
    spec_path = path.expanduser().resolve()
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    workers = payload.get("workers")
    if not isinstance(workers, list) or not workers:
        raise ValueError("wave spec requires non-empty workers list")
    if len(workers) > MAX_WAVE_WORKERS:
        raise ValueError(f"wave workers cannot exceed {MAX_WAVE_WORKERS}")
    validated = [_validate_worker(item, index) for index, item in enumerate(workers)]
    return {
        "schema": "mco.dispatch_wave_spec.v1.0",
        "title": payload.get("title") or "dispatch wave",
        "workers": validated,
        "base_dir": str(spec_path.parent),
    }


def queue_dispatch_wave(task_dir: Path, spec: dict[str, Any], require_ready: bool = False) -> dict[str, Any]:
    wave_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f-wave")
    wave_dir = task_dir / "dispatch" / "waves"
    wave_dir.mkdir(parents=True, exist_ok=True)
    dispatches = []
    base_dir = Path(str(spec.get("base_dir") or "."))
    for worker in spec["workers"]:
        sandbox = worker.get("sandbox")
        sandbox_path = None
        if sandbox:
            raw_path = Path(sandbox).expanduser()
            sandbox_path = raw_path if raw_path.is_absolute() else base_dir / raw_path
        dispatches.append(
            queue_dispatch(
                task_dir,
                worker["agent"],
                worker["title"],
                worker["instructions"],
                require_ready=require_ready,
                sandbox_path=sandbox_path.resolve() if sandbox_path else None,
            )
        )

    queued_count = sum(1 for item in dispatches if item.get("status") == "queued")
    blocked_count = sum(1 for item in dispatches if item.get("status") == "blocked")
    result = {
        "schema": "mco.dispatch_wave.v1.0",
        "wave_id": wave_id,
        "title": spec.get("title") or "dispatch wave",
        "require_ready": require_ready,
        "worker_count": len(dispatches),
        "queued_count": queued_count,
        "blocked_count": blocked_count,
        "status": "PASS" if blocked_count == 0 else "BLOCKED",
        "dispatches": dispatches,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    wave_path = wave_dir / f"{wave_id}.json"
    result["path"] = str(wave_path)
    wave_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    append_event(
        task_dir,
        "dispatch_wave_queued",
        f"Dispatch wave queued: {queued_count} queued, {blocked_count} blocked",
        {"wave_id": wave_id, "path": str(wave_path), "require_ready": require_ready},
    )
    return result
