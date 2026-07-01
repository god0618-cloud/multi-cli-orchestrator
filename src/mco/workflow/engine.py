from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.dispatch.queue import queue_dispatch
from mco.replay.ledger import append_event


def read_plan(task_dir: Path) -> dict[str, Any]:
    path = task_dir / "plan.json"
    if not path.exists():
        raise FileNotFoundError(f"plan not found: {path}")
    plan = json.loads(path.read_text(encoding="utf-8"))
    return normalize_plan(plan)


def write_plan_state(task_dir: Path, plan: dict[str, Any]) -> None:
    (task_dir / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")


def normalize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    phases = plan.get("phases") or []
    if not phases:
        raise ValueError("plan has no phases")
    first_phase = phases[0]["id"]
    plan.setdefault("status", "initialized")
    plan.setdefault("current_phase", first_phase)
    states = plan.setdefault("phase_states", {})
    for phase in phases:
        states.setdefault(
            phase["id"],
            {
                "status": "ready" if phase["id"] == plan["current_phase"] else "pending",
                "summary": None,
                "gate_results": [],
            },
        )
    return plan


def _phase_by_id(plan: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in plan["phases"]:
        if phase["id"] == phase_id:
            return phase
    raise ValueError(f"unknown phase: {phase_id}")


def _gate_result(task_dir: Path, gate: str) -> dict[str, Any]:
    if gate == "loop_spec_exists":
        ok = (task_dir / "LOOP_SPEC.json").exists()
        detail = "LOOP_SPEC.json exists" if ok else "LOOP_SPEC.json missing"
    elif gate == "run_ledger_has_events":
        ledger_path = task_dir / "RUN_LEDGER.json"
        if ledger_path.exists():
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            count = len(ledger.get("events") or [])
            ok = count > 0
            detail = f"events={count}"
        else:
            ok = False
            detail = "RUN_LEDGER.json missing"
    elif gate == "dashboard_exists":
        ok = (task_dir / "dashboard.html").exists()
        detail = "dashboard.html exists" if ok else "dashboard.html missing"
    elif gate == "sandbox_contract_not_required_for_single_worker":
        ok = True
        detail = "single-worker demo gate"
    else:
        ok = False
        detail = f"unsupported gate: {gate}"
    return {"gate": gate, "ok": ok, "detail": detail}


def evaluate_phase_gates(task_dir: Path, phase: dict[str, Any]) -> list[dict[str, Any]]:
    return [_gate_result(task_dir, gate) for gate in phase.get("gates", [])]


def workflow_status(task_dir: Path) -> dict[str, Any]:
    plan = read_plan(task_dir)
    return {
        "schema": "mco.workflow_status.v1.0",
        "workflow": plan.get("workflow"),
        "status": plan.get("status"),
        "current_phase": plan.get("current_phase"),
        "phase_states": plan.get("phase_states", {}),
    }


def advance_workflow(
    task_dir: Path,
    phase_id: str,
    verdict: str,
    summary: str,
    auto_dispatch: bool = False,
    require_ready: bool = False,
) -> dict[str, Any]:
    if verdict not in {"pass", "fail"}:
        raise ValueError("--verdict must be pass or fail")

    plan = read_plan(task_dir)
    if plan.get("status") in {"completed", "blocked"}:
        raise ValueError(f"workflow cannot advance from status: {plan.get('status')}")
    if phase_id != plan.get("current_phase"):
        raise ValueError(f"current phase is {plan.get('current_phase')}, not {phase_id}")

    phase = _phase_by_id(plan, phase_id)
    states = plan["phase_states"]
    state = states[phase_id]
    gate_results = evaluate_phase_gates(task_dir, phase)
    failed_gates = [item for item in gate_results if not item["ok"]]
    now = datetime.now(timezone.utc).isoformat()

    if verdict == "fail" or failed_gates:
        state.update(
            {
                "status": "failed",
                "summary": summary if verdict == "fail" else "Gate failure.",
                "gate_results": gate_results,
                "completed_at": now,
            }
        )
        plan["status"] = "blocked"
        plan["blocked_by"] = phase_id
        write_plan_state(task_dir, plan)
        append_event(
            task_dir,
            "workflow_phase_failed",
            f"Workflow phase failed: {phase_id}",
            {"phase": phase_id, "verdict": verdict, "gate_results": gate_results},
        )
        return {
            "schema": "mco.workflow_advance.v1.0",
            "phase": phase_id,
            "status": "blocked",
            "gate_results": gate_results,
            "next_phase": None,
            "dispatch": None,
        }

    state.update(
        {
            "status": "completed",
            "summary": summary,
            "gate_results": gate_results,
            "completed_at": now,
        }
    )

    on_pass = phase.get("on_pass")
    dispatch = None
    if on_pass == "complete":
        plan["status"] = "completed"
        plan["current_phase"] = None
        next_phase = None
    else:
        _phase_by_id(plan, str(on_pass))
        next_phase = str(on_pass)
        plan["status"] = "in_progress"
        plan["current_phase"] = next_phase
        states[next_phase]["status"] = "ready"
        if auto_dispatch:
            next_phase_payload = _phase_by_id(plan, next_phase)
            dispatch = queue_dispatch(
                task_dir,
                str(next_phase_payload.get("preferred_agent") or "generic-cli"),
                f"Workflow phase: {next_phase}",
                _dispatch_instructions(next_phase_payload),
                require_ready=require_ready,
            )

    write_plan_state(task_dir, plan)
    append_event(
        task_dir,
        "workflow_phase_passed",
        f"Workflow phase passed: {phase_id}",
        {"phase": phase_id, "next_phase": next_phase, "dispatch": dispatch},
    )
    return {
        "schema": "mco.workflow_advance.v1.0",
        "phase": phase_id,
        "status": plan["status"],
        "gate_results": gate_results,
        "next_phase": next_phase,
        "dispatch": dispatch,
    }


def _dispatch_instructions(phase: dict[str, Any]) -> str:
    gates = ", ".join(phase.get("gates", [])) or "none"
    outputs = ", ".join(phase.get("outputs", [])) or "none"
    return (
        f"Execute workflow phase `{phase['id']}` as role `{phase.get('role', 'worker')}`.\n\n"
        f"Required gates: {gates}.\n"
        f"Expected outputs: {outputs}.\n"
        "Write durable evidence before completing the dispatch."
    )
