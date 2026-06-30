from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mco.adapters.generic import generic_cli_manifest
from mco.schemas import validate_adapter_manifest, validate_sandbox_contract


@dataclass(frozen=True)
class DoctorResult:
    status: str
    checks: list[dict]

    @property
    def ok(self) -> bool:
        return self.status == "READY_SUPERVISED"

    def to_dict(self) -> dict:
        return {"status": self.status, "checks": self.checks}


def manifest_for_agent(agent: str) -> dict:
    if agent != "generic-cli":
        raise ValueError(f"unsupported adapter: {agent}")
    return generic_cli_manifest()


def read_sandbox_contract(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_sandbox_contract(payload)
    return payload


def doctor_adapter(agent: str, sandbox_path: Path | None = None) -> DoctorResult:
    checks: list[dict] = []
    manifest = manifest_for_agent(agent)
    validate_adapter_manifest(manifest)

    required_true = ["non_interactive", "supervised", "can_read_inbox", "can_write_artifacts"]
    for field in required_true:
        checks.append({"name": field, "status": "PASS" if manifest[field] is True else "FAIL", "detail": manifest[field]})

    checks.append({"name": "can_run_shell", "status": "PASS", "detail": manifest["can_run_shell"]})

    if sandbox_path is None:
        checks.append({"name": "sandbox_contract", "status": "WARN", "detail": "not provided"})
    else:
        try:
            sandbox = read_sandbox_contract(sandbox_path)
            if sandbox["agent"] != agent:
                checks.append({"name": "sandbox_agent", "status": "FAIL", "detail": sandbox["agent"]})
            else:
                checks.append({"name": "sandbox_agent", "status": "PASS", "detail": agent})
            if sandbox["credential_policy"] != "no credentials":
                checks.append({"name": "credential_policy", "status": "FAIL", "detail": sandbox["credential_policy"]})
            else:
                checks.append({"name": "credential_policy", "status": "PASS", "detail": "no credentials"})
        except Exception as exc:
            checks.append({"name": "sandbox_contract", "status": "FAIL", "detail": str(exc)})

    has_fail = any(check["status"] == "FAIL" for check in checks)
    has_warn = any(check["status"] == "WARN" for check in checks)
    if has_fail:
        status = "BLOCKED"
    elif has_warn:
        status = "READY_MANUAL"
    else:
        status = "READY_SUPERVISED"
    return DoctorResult(status=status, checks=checks)
