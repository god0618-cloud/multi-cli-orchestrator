from __future__ import annotations

import json
from pathlib import Path


def default_templates_dir() -> Path:
    source_tree_dir = Path(__file__).resolve().parents[3] / "templates" / "workflows"
    if source_tree_dir.exists():
        return source_tree_dir
    return Path(__file__).resolve().parents[1] / "templates" / "workflows"


def load_workflow_template(name: str, templates_dir: Path | None = None) -> dict:
    base = templates_dir or default_templates_dir()
    path = base / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"workflow template not found: {name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_workflow_template(payload)
    return payload


def validate_workflow_template(payload: dict) -> None:
    required = {"schema", "name", "phases"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"workflow template missing required keys: {', '.join(missing)}")
    if not isinstance(payload["phases"], list) or not payload["phases"]:
        raise ValueError("workflow template phases must be a non-empty list")
    for index, phase in enumerate(payload["phases"]):
        for key in ["id", "role", "gates", "outputs"]:
            if key not in phase:
                raise ValueError(f"workflow phase {index} missing key: {key}")


def write_plan(task_dir: Path, template: dict) -> Path:
    plan = {
        "schema": "mco.plan.v0.2",
        "workflow": template["name"],
        "phases": template["phases"],
        "status": "initialized",
    }
    out = task_dir / "plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return out
