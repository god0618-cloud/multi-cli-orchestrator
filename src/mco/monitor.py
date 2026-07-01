from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.config import WorkspaceConfig
from mco.replay.ledger import append_event, register_artifact
from mco.status import build_status_snapshot
from mco.task.lifecycle import task_dir


MAX_CYCLES = 24
MAX_INTERVAL_SECONDS = 3600


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _validate_bounds(cycles: int, interval_seconds: float) -> None:
    if cycles < 1:
        raise ValueError("--cycles must be >= 1")
    if cycles > MAX_CYCLES:
        raise ValueError(f"--cycles must be <= {MAX_CYCLES}")
    if interval_seconds < 0:
        raise ValueError("--interval-seconds must be >= 0")
    if interval_seconds > MAX_INTERVAL_SECONDS:
        raise ValueError(f"--interval-seconds must be <= {MAX_INTERVAL_SECONDS}")


def run_monitor(
    config: WorkspaceConfig,
    task_id: str,
    cycles: int = 1,
    interval_seconds: float = 0,
    include_audit: bool = False,
    include_doctor: bool = False,
) -> dict[str, Any]:
    _validate_bounds(cycles, interval_seconds)
    directory = task_dir(config, task_id)
    snapshot_dir = directory / "artifacts" / "status-snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    snapshots = []
    exit_code = 0
    for index in range(cycles):
        snapshot = build_status_snapshot(
            config,
            task_id=task_id,
            include_audit=include_audit,
            include_doctor=include_doctor,
        )
        payload = dict(snapshot.payload)
        payload["monitor"] = {
            "cycle": index + 1,
            "cycles": cycles,
            "interval_seconds": interval_seconds,
        }
        out = snapshot_dir / f"{_stamp()}-cycle-{index + 1}.json"
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        register_artifact(directory, out, f"status-snapshot-cycle-{index + 1}")
        append_event(
            directory,
            "status_snapshot",
            f"Status snapshot cycle {index + 1}/{cycles} generated.",
            {"artifact": str(out), "doctor_probe": include_doctor, "audit": include_audit},
        )
        snapshots.append(str(out))

        audit = payload.get("audit")
        if audit is not None and not audit.get("ok", False):
            exit_code = 1

        if index < cycles - 1 and interval_seconds > 0:
            time.sleep(interval_seconds)

    return {
        "schema": "mco.monitor.v1.0",
        "task_id": task_id,
        "cycles": cycles,
        "interval_seconds": interval_seconds,
        "doctor_probe": include_doctor,
        "audit": include_audit,
        "snapshots": snapshots,
        "exit_code": exit_code,
    }
