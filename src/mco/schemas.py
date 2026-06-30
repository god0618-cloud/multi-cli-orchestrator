from __future__ import annotations


LOOP_SPEC_REQUIRED_KEYS = {
    "goal",
    "inputs",
    "allowed_actions",
    "forbidden_actions",
    "verification",
    "stop_condition",
    "evidence_to_write",
    "escalation_triggers",
}

SANDBOX_CONTRACT_REQUIRED_KEYS = {
    "worker_id",
    "agent",
    "write_scope",
    "read_scope",
    "ports",
    "data_boundary",
    "credential_policy",
    "merge_owner",
    "verification_artifacts",
}

RUN_LEDGER_REQUIRED_KEYS = {
    "run_id",
    "task_id",
    "request",
    "workflow",
    "loop_spec_ref",
    "sandbox_contract_refs",
    "events",
    "artifacts",
    "decisions",
    "rejected_branches",
    "final_verdict",
}

ADAPTER_MANIFEST_REQUIRED_KEYS = {
    "agent",
    "adapter_type",
    "interactive",
    "non_interactive",
    "supervised",
    "can_read_inbox",
    "can_write_artifacts",
    "can_run_shell",
    "can_use_browser",
    "quota_status",
}


def default_loop_spec() -> dict:
    return {
        "schema": "mco.loop_spec.v0.2",
        "goal": "",
        "inputs": [],
        "allowed_actions": [],
        "forbidden_actions": [],
        "verification": [],
        "stop_condition": "",
        "evidence_to_write": [],
        "escalation_triggers": [],
    }


def validate_loop_spec(payload: dict) -> None:
    missing = sorted(LOOP_SPEC_REQUIRED_KEYS - payload.keys())
    if missing:
        raise ValueError(f"loop spec missing required keys: {', '.join(missing)}")
    list_fields = [
        "inputs",
        "allowed_actions",
        "forbidden_actions",
        "verification",
        "evidence_to_write",
        "escalation_triggers",
    ]
    for field in list_fields:
        if not isinstance(payload[field], list):
            raise TypeError(f"loop spec field must be list: {field}")


def validate_sandbox_contract(payload: dict) -> None:
    missing = sorted(SANDBOX_CONTRACT_REQUIRED_KEYS - payload.keys())
    if missing:
        raise ValueError(f"sandbox contract missing required keys: {', '.join(missing)}")
    for field in ["write_scope", "read_scope", "ports", "verification_artifacts"]:
        if not isinstance(payload[field], list):
            raise TypeError(f"sandbox contract field must be list: {field}")


def validate_adapter_manifest(payload: dict) -> None:
    missing = sorted(ADAPTER_MANIFEST_REQUIRED_KEYS - payload.keys())
    if missing:
        raise ValueError(f"adapter manifest missing required keys: {', '.join(missing)}")
    for field in [
        "interactive",
        "non_interactive",
        "supervised",
        "can_read_inbox",
        "can_write_artifacts",
        "can_run_shell",
        "can_use_browser",
    ]:
        if not isinstance(payload[field], bool):
            raise TypeError(f"adapter manifest field must be bool: {field}")


def default_sandbox_contract() -> dict:
    return {
        "schema": "mco.sandbox_contract.v0.2",
        "worker_id": "",
        "agent": "",
        "write_scope": [],
        "read_scope": [],
        "ports": [],
        "data_boundary": "",
        "credential_policy": "",
        "merge_owner": "",
        "verification_artifacts": [],
    }


def default_run_ledger() -> dict:
    return {
        "schema": "mco.run_ledger.v0.2",
        "run_id": "",
        "task_id": "",
        "request": "",
        "workflow": "",
        "loop_spec_ref": "",
        "sandbox_contract_refs": [],
        "events": [],
        "artifacts": [],
        "decisions": [],
        "rejected_branches": [],
        "final_verdict": "",
    }


def validate_run_ledger(payload: dict) -> None:
    missing = sorted(RUN_LEDGER_REQUIRED_KEYS - payload.keys())
    if missing:
        raise ValueError(f"run ledger missing required keys: {', '.join(missing)}")
    for field in ["sandbox_contract_refs", "events", "artifacts", "decisions", "rejected_branches"]:
        if not isinstance(payload[field], list):
            raise TypeError(f"run ledger field must be list: {field}")
