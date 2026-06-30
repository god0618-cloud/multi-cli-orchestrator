from __future__ import annotations

import json
from pathlib import Path

from mco.replay.ledger import read_ledger


def replay_ledger(path: Path, *, json_output: bool = False) -> str:
    ledger = read_ledger(path)
    events = ledger.get("events", [])
    artifacts = ledger.get("artifacts", [])
    sandbox_refs = ledger.get("sandbox_contract_refs", [])
    if json_output:
        return json.dumps(
            {
                "schema": "mco.replay.v0.5",
                "task_id": ledger.get("task_id"),
                "run_id": ledger.get("run_id"),
                "workflow": ledger.get("workflow"),
                "event_count": len(events),
                "artifact_count": len(artifacts),
                "events": events,
                "artifacts": artifacts,
                "sandbox_contract_refs": sandbox_refs,
                "final_verdict": ledger.get("final_verdict"),
            },
            indent=2,
        )

    lines = [
        f"Run replay: {ledger.get('run_id') or '-'}",
        f"Task: {ledger.get('task_id') or '-'}",
        f"Workflow: {ledger.get('workflow') or '-'}",
        f"Final verdict: {ledger.get('final_verdict') or '-'}",
        "",
        "Timeline:",
    ]
    for index, event in enumerate(events, start=1):
        at = event.get("at", "-")
        event_type = event.get("type", "-")
        message = event.get("message", "")
        lines.append(f"{index:02d}. {at} [{event_type}] {message}")

    lines.extend(["", "Artifacts:"])
    for artifact in artifacts:
        if isinstance(artifact, dict):
            label = artifact.get("label", "artifact")
            artifact_path = artifact.get("path", "")
            lines.append(f"- {label}: {artifact_path}")
        else:
            lines.append(f"- {artifact}")
    lines.extend(["", "Sandbox contracts:"])
    for ref in sandbox_refs:
        lines.append(f"- {ref}")
    return "\n".join(lines)
