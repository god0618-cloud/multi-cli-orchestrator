from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mco.adapters.matrix import build_adapter_matrix


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    agent: str
    readiness: str
    reason: str
    blockers: list[str]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "agent": self.agent,
            "readiness": self.readiness,
            "reason": self.reason,
            "blockers": self.blockers,
        }


def evaluate_adapter_gate(agent: str, sandbox_path: Path | None = None) -> GateResult:
    matrix = build_adapter_matrix(include_doctor=True)
    rows = {row["agent"]: row for row in matrix["agents"]}
    row = rows.get(agent)
    if row is None:
        return GateResult(
            allowed=False,
            agent=agent,
            readiness="UNKNOWN",
            reason="adapter is not known to the matrix",
            blockers=["unknown adapter"],
        )

    readiness = str(row.get("readiness", "UNKNOWN"))
    blockers = list(row.get("promotion_blockers") or [])
    if readiness != "READY_SUPERVISED":
        reason = f"adapter readiness is {readiness}, not READY_SUPERVISED"
        return GateResult(False, agent, readiness, reason, blockers or [reason])

    sandbox_template = row.get("sandbox_template")
    if sandbox_template and sandbox_path is not None and sandbox_path.resolve() != Path(str(sandbox_template)).resolve():
        # A custom sandbox can still be valid at execution time. The gate records the difference but does not block.
        blockers = blockers + [f"custom sandbox provided: {sandbox_path}"]

    return GateResult(True, agent, readiness, "adapter is READY_SUPERVISED", blockers)
