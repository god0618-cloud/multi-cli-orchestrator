from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def read_ledger(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_ledger(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def append_event(task_dir: Path, event_type: str, message: str, data: dict | None = None) -> dict:
    ledger_path = task_dir / "RUN_LEDGER.json"
    ledger = read_ledger(ledger_path)
    event = {
        "type": event_type,
        "at": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }
    if data:
        event["data"] = data
    ledger.setdefault("events", []).append(event)
    write_ledger(ledger_path, ledger)
    return event


def set_workflow(task_dir: Path, workflow: str) -> None:
    ledger_path = task_dir / "RUN_LEDGER.json"
    ledger = read_ledger(ledger_path)
    ledger["workflow"] = workflow
    write_ledger(ledger_path, ledger)


def add_sandbox_contract_ref(task_dir: Path, sandbox_path: Path) -> None:
    ledger_path = task_dir / "RUN_LEDGER.json"
    ledger = read_ledger(ledger_path)
    ref = str(sandbox_path.resolve())
    refs = ledger.setdefault("sandbox_contract_refs", [])
    if ref not in refs:
        refs.append(ref)
    write_ledger(ledger_path, ledger)


def register_artifact(task_dir: Path, artifact_path: Path, label: str | None = None) -> dict:
    ledger_path = task_dir / "RUN_LEDGER.json"
    ledger = read_ledger(ledger_path)
    artifact = {
        "path": str(artifact_path.resolve()),
        "label": label or artifact_path.name,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    ledger.setdefault("artifacts", []).append(artifact)
    ledger.setdefault("events", []).append(
        {
            "type": "artifact_registered",
            "at": artifact["registered_at"],
            "message": f"Artifact registered: {artifact['label']}",
            "data": {"path": artifact["path"]},
        }
    )
    write_ledger(ledger_path, ledger)
    return artifact
