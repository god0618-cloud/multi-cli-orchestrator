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
    manifest = payload.get("manifest")
    if manifest is not None:
        _validate_manifest(manifest)
    if not isinstance(payload["phases"], list) or not payload["phases"]:
        raise ValueError("workflow template phases must be a non-empty list")
    for index, phase in enumerate(payload["phases"]):
        for key in ["id", "role", "gates", "outputs"]:
            if key not in phase:
                raise ValueError(f"workflow phase {index} missing key: {key}")


def _validate_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("workflow template manifest must be an object")
    required = {
        "trigger",
        "scope",
        "required_inputs",
        "artifacts",
        "verification",
        "stop_conditions",
        "failure_modes",
    }
    missing = sorted(required - manifest.keys())
    if missing:
        raise ValueError(f"workflow template manifest missing required keys: {', '.join(missing)}")
    for key in ["required_inputs", "artifacts", "verification", "stop_conditions", "failure_modes"]:
        if not isinstance(manifest[key], list) or not manifest[key]:
            raise ValueError(f"workflow template manifest {key} must be a non-empty list")
    if "plan_review_required" in manifest and not isinstance(manifest["plan_review_required"], bool):
        raise ValueError("workflow template manifest plan_review_required must be a boolean")
    if "evidence_level" in manifest and manifest["evidence_level"] not in {"L1", "L2", "L3"}:
        raise ValueError("workflow template manifest evidence_level must be one of L1, L2, L3")
    if "stack" in manifest and manifest["stack"] not in {"single", "dual"}:
        raise ValueError("workflow template manifest stack must be one of single, dual")
    budget = manifest.get("budget")
    if budget is not None:
        _validate_budget(budget)
    fanout_policy = manifest.get("fanout_policy")
    if fanout_policy is not None and not isinstance(fanout_policy, dict):
        raise ValueError("workflow template manifest fanout_policy must be an object")


def _validate_budget(budget: dict) -> None:
    if not isinstance(budget, dict):
        raise ValueError("workflow template manifest budget must be an object")
    for key in ["avg_token_cost", "hard_cap"]:
        if key in budget and (not isinstance(budget[key], int) or budget[key] < 0):
            raise ValueError(f"workflow template manifest budget {key} must be a non-negative integer")
    if "defer_policy" in budget and not isinstance(budget["defer_policy"], str):
        raise ValueError("workflow template manifest budget defer_policy must be a string")


def write_plan(task_dir: Path, template: dict) -> Path:
    first_phase = template["phases"][0]["id"]
    plan = {
        "schema": "mco.plan.v0.2",
        "workflow": template["name"],
        "manifest": template.get("manifest"),
        "phases": template["phases"],
        "status": "initialized",
        "current_phase": first_phase,
        "phase_states": {
            phase["id"]: {
                "status": "ready" if phase["id"] == first_phase else "pending",
                "summary": None,
                "gate_results": [],
            }
            for phase in template["phases"]
        },
    }
    out = task_dir / "plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return out
