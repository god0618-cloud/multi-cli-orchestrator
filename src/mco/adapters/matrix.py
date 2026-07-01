from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.adapters.doctor import doctor_adapter, manifest_for_agent


KNOWN_AGENTS = ["generic-cli", "claude-code", "kimi-code", "mimo-code", "codewhale"]
IMPLEMENTED_AGENTS = {"generic-cli", "claude-code", "kimi-code"}
SMOKE_AGENTS = {"claude-code", "kimi-code"}
BUDGET_CAPABLE_AGENTS = {"claude-code"}

RECOMMENDED_USE = {
    "generic-cli": "deterministic local commands inside sandbox contracts",
    "claude-code": "supervised non-interactive reasoning, controller, and implementation tasks",
    "kimi-code": "supervised non-interactive frontend and UI implementation tasks",
    "mimo-code": "manual research/ammo collection until non-interactive evidence exists",
    "codewhale": "manual red-team or DeepSeek-style review until adapter evidence exists",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _template_path(agent: str) -> Path:
    return _repo_root() / "templates" / "adapters" / f"{agent}.disabled.json"


def _sandbox_template(agent: str) -> Path | None:
    if agent == "generic-cli":
        path = _repo_root() / "templates" / "sandbox-contracts" / "single-worker.json"
        return path if path.exists() else None
    path = _repo_root() / "templates" / "sandbox-contracts" / f"{agent}-supervised.json"
    return path if path.exists() else None


def _disabled_manifest(agent: str) -> dict[str, Any]:
    path = _template_path(agent)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "schema": "mco.adapter_manifest.v1.2",
        "agent": agent,
        "adapter_type": "missing-template",
        "interactive": True,
        "non_interactive": False,
        "supervised": False,
        "can_read_inbox": False,
        "can_write_artifacts": False,
        "can_run_shell": False,
        "can_use_browser": False,
        "quota_status": "unknown",
    }


def _manifest_for_matrix(agent: str) -> dict[str, Any]:
    if agent in IMPLEMENTED_AGENTS:
        return manifest_for_agent(agent)
    return _disabled_manifest(agent)


def _readiness(manifest: dict[str, Any], doctor_status: str | None) -> str:
    if doctor_status:
        return doctor_status
    if manifest.get("supervised") is True and manifest.get("non_interactive") is True:
        return "IMPLEMENTED_NOT_PROBED"
    return "DISABLED"


def _promotion_blockers(agent: str, manifest: dict[str, Any], doctor_status: str | None) -> list[str]:
    blockers: list[str] = []
    if manifest.get("supervised") is not True:
        blockers.append("supervised adapter not implemented")
    if manifest.get("non_interactive") is not True:
        blockers.append("non-interactive command contract missing")
    if manifest.get("can_read_inbox") is not True or manifest.get("can_write_artifacts") is not True:
        blockers.append("task inbox/artifact participation missing")
    if manifest.get("quota_status") == "unknown" and agent in {"mimo-code", "codewhale"}:
        blockers.append("quota semantics unknown")
    if agent not in SMOKE_AGENTS and agent != "generic-cli":
        blockers.append("opt-in smoke gate missing")
    if doctor_status == "BLOCKED":
        blockers.append("adapter doctor blocked")
    return blockers


def _execution_mode(manifest: dict[str, Any]) -> str:
    if manifest.get("non_interactive") is True and manifest.get("supervised") is True:
        return "supervised_non_interactive"
    if manifest.get("interactive") is True:
        return "manual_interactive"
    return "disabled"


def _automation_posture(agent: str, manifest: dict[str, Any], doctor_status: str | None) -> str:
    if doctor_status == "READY_SUPERVISED":
        return "auto_dispatch_allowed_with_require_ready"
    if agent in IMPLEMENTED_AGENTS and manifest.get("non_interactive") is True:
        return "implemented_but_probe_before_auto_dispatch"
    return "manual_only_do_not_auto_dispatch"


def build_adapter_matrix(include_doctor: bool = False) -> dict[str, Any]:
    rows = []
    for agent in KNOWN_AGENTS:
        manifest = _manifest_for_matrix(agent)
        sandbox_path = _sandbox_template(agent)
        doctor_status = None
        doctor_checks = []
        if include_doctor and agent in IMPLEMENTED_AGENTS:
            try:
                result = doctor_adapter(agent, sandbox_path)
                doctor_status = result.status
                doctor_checks = result.checks
            except Exception as exc:
                doctor_status = "BLOCKED"
                doctor_checks = [{"name": "doctor_exception", "status": "FAIL", "detail": str(exc)}]

        row = {
            "agent": agent,
            "adapter_type": manifest.get("adapter_type", "unknown"),
            "implemented": agent in IMPLEMENTED_AGENTS,
            "readiness": _readiness(manifest, doctor_status),
            "execution_mode": _execution_mode(manifest),
            "automation_posture": _automation_posture(agent, manifest, doctor_status),
            "recommended_use": RECOMMENDED_USE.get(agent, "unknown"),
            "interactive": manifest.get("interactive"),
            "non_interactive": manifest.get("non_interactive"),
            "supervised": manifest.get("supervised"),
            "can_read_inbox": manifest.get("can_read_inbox"),
            "can_write_artifacts": manifest.get("can_write_artifacts"),
            "can_run_shell": manifest.get("can_run_shell"),
            "can_use_browser": manifest.get("can_use_browser"),
            "quota_status": manifest.get("quota_status", "unknown"),
            "per_run_budget_cap": agent in BUDGET_CAPABLE_AGENTS,
            "smoke_gate": agent in SMOKE_AGENTS,
            "sandbox_template": str(sandbox_path) if sandbox_path else None,
            "safe_command_allowlist": manifest.get("safe_command_allowlist", []),
            "doctor_status": doctor_status,
            "doctor_checks": doctor_checks,
            "promotion_blockers": _promotion_blockers(agent, manifest, doctor_status),
        }
        rows.append(row)

    return {
        "schema": "mco.adapter_matrix.v1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "include_doctor": include_doctor,
        "claims": [
            "Implemented means the adapter has an executable code path in this package.",
            "READY_SUPERVISED requires doctor probing and sandbox validation.",
            "manual_only_do_not_auto_dispatch means the CLI can still participate through a human-run window, but should not receive automated dispatches.",
            "quota_status=unknown is preserved unless adapter-specific evidence proves a narrower claim.",
            "Real smoke commands are always explicit opt-in and are not part of release checks.",
        ],
        "agents": rows,
    }


def write_adapter_matrix(output_json: Path, output_html: Path | None = None, include_doctor: bool = False) -> dict[str, str]:
    matrix = build_adapter_matrix(include_doctor=include_doctor)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    result = {"json": str(output_json)}
    if output_html is not None:
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(render_adapter_matrix_html(matrix), encoding="utf-8")
        result["html"] = str(output_html)
    return result


def _pill(value: Any) -> str:
    text = str(value)
    cls = "ok" if text in {"True", "READY_SUPERVISED", "IMPLEMENTED_NOT_PROBED", "budget_limited", "not_applicable"} else "warn"
    if text in {"False", "DISABLED", "BLOCKED"}:
        cls = "bad"
    if text == "unknown":
        cls = "warn"
    return f"<span class=\"pill {cls}\">{html.escape(text)}</span>"


def render_adapter_matrix_html(matrix: dict[str, Any]) -> str:
    rows = []
    for item in matrix["agents"]:
        blockers = item.get("promotion_blockers") or []
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(item['agent'])}</strong><br><span>{html.escape(item['adapter_type'])}</span></td>"
            f"<td>{_pill(item['readiness'])}</td>"
            f"<td>{html.escape(item['execution_mode'])}<br><small>{html.escape(item['automation_posture'])}</small></td>"
            f"<td>{_pill(item['non_interactive'])}</td>"
            f"<td>{_pill(item['supervised'])}</td>"
            f"<td>{_pill(item['quota_status'])}<br><small>budget cap: {html.escape(str(item['per_run_budget_cap']))}</small></td>"
            f"<td>{_pill(item['smoke_gate'])}</td>"
            f"<td>{html.escape(item['recommended_use'])}<br><small>{html.escape('; '.join(blockers) if blockers else 'none')}</small></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCO Adapter Matrix</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #0f172a; color: #e5e7eb; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px; }}
    h1 {{ margin-bottom: 4px; }}
    p {{ color: #94a3b8; }}
    table {{ width: 100%; border-collapse: collapse; background: #111827; border: 1px solid #1f2937; border-radius: 12px; overflow: hidden; }}
    th, td {{ padding: 14px; border-bottom: 1px solid #1f2937; text-align: left; vertical-align: top; }}
    th {{ color: #cbd5e1; font-size: 13px; text-transform: uppercase; letter-spacing: .05em; }}
    span {{ color: #94a3b8; font-size: 13px; }}
    small {{ color: #94a3b8; }}
    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
    .ok {{ color: #bbf7d0; background: #14532d; }}
    .warn {{ color: #fde68a; background: #713f12; }}
    .bad {{ color: #fecaca; background: #7f1d1d; }}
  </style>
</head>
<body>
  <main>
    <h1>Adapter Matrix</h1>
    <p>Generated at {html.escape(matrix['generated_at'])}. Doctor probing: {html.escape(str(matrix['include_doctor']))}.</p>
    <table>
      <thead><tr><th>Agent</th><th>Readiness</th><th>Execution Mode</th><th>Non-interactive</th><th>Supervised</th><th>Quota</th><th>Smoke</th><th>Use / Promotion Blockers</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </main>
</body>
</html>
"""
