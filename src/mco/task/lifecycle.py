from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mco.config import WorkspaceConfig
from mco.schemas import default_loop_spec, default_run_ledger, validate_loop_spec


TASK_ID_RE = re.compile(r"[^a-zA-Z0-9-]+")


@dataclass(frozen=True)
class CreatedTask:
    task_id: str
    task_dir: Path
    loop_spec_path: Path
    run_ledger_path: Path


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def slugify_title(title: str) -> str:
    slug = TASK_ID_RE.sub("-", title.strip().lower()).strip("-")
    return slug[:48] or "task"


def create_task(config: WorkspaceConfig, title: str, request: str | None = None) -> CreatedTask:
    task_id = f"{utc_stamp()}-{slugify_title(title)}"
    task_dir = config.tasks_dir / task_id
    artifacts_dir = task_dir / "artifacts"
    task_dir.mkdir(parents=True, exist_ok=False)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "schema": "mco.task.v0.2",
        "task_id": task_id,
        "title": title,
        "request": request or title,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_dir": str(artifacts_dir),
    }
    (task_dir / "task.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    loop_spec = default_loop_spec()
    loop_spec.update(
        {
            "goal": title,
            "inputs": [{"type": "request", "value": request or title}],
            "allowed_actions": ["write within this task workspace", "create evidence artifacts"],
            "forbidden_actions": [
                "write outside configured workspace without explicit gate",
                "write native CLI memory",
                "write stable knowledge base",
                "perform destructive actions",
            ],
            "verification": ["task metadata exists", "run ledger records task_created event"],
            "stop_condition": "task is ready for workflow planning",
            "evidence_to_write": ["task.json", "LOOP_SPEC.json", "RUN_LEDGER.json"],
            "escalation_triggers": ["missing workspace config", "unsafe write request"],
        }
    )
    validate_loop_spec(loop_spec)
    loop_spec_path = task_dir / "LOOP_SPEC.json"
    loop_spec_path.write_text(json.dumps(loop_spec, indent=2) + "\n", encoding="utf-8")

    ledger = default_run_ledger()
    ledger.update(
        {
            "run_id": task_id,
            "task_id": task_id,
            "request": request or title,
            "workflow": "unplanned",
            "loop_spec_ref": str(loop_spec_path),
            "events": [
                {
                    "type": "task_created",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "message": "Task created with default loop spec.",
                }
            ],
            "artifacts": [str(task_dir / "task.json"), str(loop_spec_path)],
            "final_verdict": "open",
        }
    )
    run_ledger_path = task_dir / "RUN_LEDGER.json"
    run_ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    return CreatedTask(
        task_id=task_id,
        task_dir=task_dir,
        loop_spec_path=loop_spec_path,
        run_ledger_path=run_ledger_path,
    )


def list_tasks(config: WorkspaceConfig) -> list[dict]:
    if not config.tasks_dir.exists():
        return []
    tasks = []
    for task_json in sorted(config.tasks_dir.glob("*/task.json")):
        tasks.append(json.loads(task_json.read_text(encoding="utf-8")))
    return tasks


def read_task(config: WorkspaceConfig, task_id: str) -> dict:
    task_json = config.tasks_dir / task_id / "task.json"
    if not task_json.exists():
        raise FileNotFoundError(f"task not found: {task_id}")
    return json.loads(task_json.read_text(encoding="utf-8"))


def task_dir(config: WorkspaceConfig, task_id: str) -> Path:
    directory = config.tasks_dir / task_id
    if not directory.exists():
        raise FileNotFoundError(f"task not found: {task_id}")
    return directory
