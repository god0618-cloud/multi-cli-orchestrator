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
        raise ValueError("supervised adapter execution does not allow port access")
    if agent == "generic-cli" and sandbox["credential_policy"] != "no credentials":
        raise ValueError("generic-cli credential_policy must be: no credentials")
    if agent == "claude-code" and sandbox["credential_policy"] != "host CLI auth only":
        raise ValueError("claude-code credential_policy must be: host CLI auth only")
    if agent == "kimi-code" and sandbox["credential_policy"] != "host CLI auth only":
        raise ValueError("kimi-code credential_policy must be: host CLI auth only")
    return sandbox
