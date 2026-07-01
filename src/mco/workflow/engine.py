from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.dispatch.queue import list_dispatches
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


def _ledger(task_dir: Path) -> dict[str, Any]:
    path = task_dir / "RUN_LEDGER.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_matches(artifact: dict[str, Any], expected: str) -> bool:
    return artifact.get("label") == expected or Path(str(artifact.get("path", ""))).name == expected


def _gate_result(task_dir: Path, gate: str) -> dict[str, Any]:
    ledger = _ledger(task_dir)
    dispatches = list_dispatches(task_dir)
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
    elif gate.startswith("file_exists:"):
        expected = gate.split(":", 1)[1]
        path = (task_dir / expected).resolve()
        ok = path.exists() and task_dir.resolve() in path.parents
        detail = f"{expected} exists" if ok else f"{expected} missing"
    elif gate.startswith("artifact_registered:"):
        expected = gate.split(":", 1)[1]
        artifacts = ledger.get("artifacts") or []
        ok = any(isinstance(item, dict) and _artifact_matches(item, expected) for item in artifacts)
        detail = f"artifact registered: {expected}" if ok else f"artifact not registered: {expected}"
    elif gate.startswith("ledger_event:"):
        expected = gate.split(":", 1)[1]
        events = ledger.get("events") or []
        count = sum(1 for item in events if isinstance(item, dict) and item.get("type") == expected)
        ok = count > 0
        detail = f"{expected} events={count}"
    elif gate.startswith("user_decision:"):
        expected = gate.split(":", 1)[1]
        decisions = ledger.get("decisions") or []
        ok = any(isinstance(item, dict) and item.get("id") == expected and item.get("status") == "approved" for item in decisions)
        detail = f"user decision approved: {expected}" if ok else f"user decision required: {expected}"
    elif gate == "all_dispatches_terminal":
        non_terminal = [item["dispatch_id"] for item in dispatches if item.get("status") in {"queued", "claimed"}]
        ok = not non_terminal
        detail = "all dispatches terminal" if ok else f"non-terminal dispatches={len(non_terminal)}"
    elif gate == "no_failed_dispatches":
        failed = [item["dispatch_id"] for item in dispatches if item.get("status") == "failed"]
        ok = not failed
        detail = "failed dispatches=0" if ok else f"failed dispatches={len(failed)}"
    elif gate == "no_blocked_dispatches":
        blocked = [item["dispatch_id"] for item in dispatches if item.get("status") == "blocked"]
        ok = not blocked
        detail = "blocked dispatches=0" if ok else f"blocked dispatches={len(blocked)}"
    elif gate.startswith("dispatch_status_count:"):
        _, status, raw_minimum = gate.split(":", 2)
        minimum = int(raw_minimum)
        count = sum(1 for item in dispatches if item.get("status") == status)
        ok = count >= minimum
        detail = f"{status} dispatches={count}, required>={minimum}"
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


def observe_workflow(task_dir: Path) -> dict[str, Any]:
    plan = read_plan(task_dir)
    dispatches = list_dispatches(task_dir)
    counts: dict[str, int] = {}
    for dispatch in dispatches:
        status = str(dispatch.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1

    if plan.get("status") == "completed":
        action = "complete"
        reason = "workflow completed"
        gate_results: list[dict[str, Any]] = []
    elif plan.get("status") == "blocked":
        action = "escalate"
        reason = f"workflow blocked by {plan.get('blocked_by')}"
        gate_results = []
    elif counts.get("blocked", 0) or counts.get("failed", 0):
        action = "escalate"
        reason = "dispatch failure or gate block exists"
        gate_results = []
    elif counts.get("queued", 0) or counts.get("claimed", 0):
        action = "wait"
        reason = "waiting for non-terminal dispatches"
        gate_results = []
    else:
        current_phase = plan.get("current_phase")
        phase = _phase_by_id(plan, str(current_phase))
        gate_results = evaluate_phase_gates(task_dir, phase)
        failed_gates = [item for item in gate_results if not item["ok"]]
        if not failed_gates:
            action = "advance"
            reason = f"current phase gates pass: {current_phase}"
        elif any(str(item["gate"]).startswith("user_decision:") for item in failed_gates):
            action = "escalate"
            reason = "user decision gate is required"
        else:
            action = "wait"
            reason = "waiting for required evidence"

    return {
        "schema": "mco.workflow_observe.v1.0",
        "workflow": plan.get("workflow"),
        "status": plan.get("status"),
        "current_phase": plan.get("current_phase"),
        "recommended_action": action,
        "reason": reason,
        "dispatch_counts": counts,
        "gate_results": gate_results,
    }


def run_workflow_loop(
    task_dir: Path,
    max_steps: int = 1,
    auto_dispatch: bool = False,
    require_ready: bool = False,
) -> dict[str, Any]:
    if max_steps < 1 or max_steps > 24:
        raise ValueError("--max-steps must be between 1 and 24")

    observations = []
    advances = []
    final_action = "wait"
    stop_reason = "max steps reached"

    for _ in range(max_steps):
        observation = observe_workflow(task_dir)
        observations.append(observation)
        action = observation["recommended_action"]
        final_action = action
        if action != "advance":
            stop_reason = observation["reason"]
            break

        phase_id = str(observation["current_phase"])
        advanced = advance_workflow(
            task_dir,
            phase_id,
            "pass",
            "Loop advanced after gates passed.",
            auto_dispatch=auto_dispatch,
            require_ready=require_ready,
        )
        advances.append(advanced)
        final_action = advanced["status"]
        if advanced["status"] in {"blocked", "completed"}:
            stop_reason = advanced["status"]
            break
    else:
        append_event(
            task_dir,
            "workflow_loop_stopped",
            "Workflow loop stopped after max steps.",
            {"max_steps": max_steps, "auto_dispatch": auto_dispatch, "require_ready": require_ready},
        )

    result = {
        "schema": "mco.workflow_loop.v1.0",
        "max_steps": max_steps,
        "steps_taken": len(advances),
        "final_action": final_action,
        "stop_reason": stop_reason,
        "observations": observations,
        "advances": advances,
    }
    append_event(
        task_dir,
        "workflow_loop_observed",
        f"Workflow loop stopped: {stop_reason}",
        {"steps_taken": len(advances), "final_action": final_action},
    )
    return result


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
