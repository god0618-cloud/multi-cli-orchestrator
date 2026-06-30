from __future__ import annotations

from pathlib import Path

from mco.adapters.doctor import doctor_adapter, read_sandbox_contract


def enforce_sandbox(agent: str, sandbox_path: Path) -> dict:
    sandbox = read_sandbox_contract(sandbox_path)
    result = doctor_adapter(agent, sandbox_path)
    if not result.ok:
        raise ValueError(f"adapter is not ready for supervised execution: {result.status}")
    if "task workspace only" not in sandbox["write_scope"]:
        raise ValueError("sandbox write_scope must include: task workspace only")
    if "task workspace only" not in sandbox["read_scope"]:
        raise ValueError("sandbox read_scope must include: task workspace only")
    if sandbox["ports"]:
        raise ValueError("generic-cli v1.0 supervised execution does not allow port access")
    return sandbox
