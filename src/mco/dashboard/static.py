from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.adapters.matrix import build_adapter_matrix
from mco.config import WorkspaceConfig


TERMINAL_PROBLEM_STATUSES = {"blocked", "failed"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _artifact_path(item: Any) -> Path | None:
    if isinstance(item, dict) and item.get("path"):
        return Path(str(item["path"]))
    return None


def _load_artifact_reports(artifacts: list[Any]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for artifact in artifacts:
        path = _artifact_path(artifact)
        if path is None or path.suffix != ".json" or not path.exists():
            continue
        payload = _read_json(path)
        if payload:
            payload["_artifact_label"] = artifact.get("label", path.name) if isinstance(artifact, dict) else path.name
            payload["_artifact_path"] = str(path)
            reports.append(payload)
    return reports


def _parse_claude_stdout(report: dict[str, Any]) -> dict[str, Any]:
    stdout = str(report.get("stdout", "")).strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


def _display_money(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"${float(value):.4f}"


def _status_class(status: str) -> str:
    normalized = status.lower()
    if normalized in {"completed", "ready", "ready_supervised", "pass"}:
        return "ok"
    if normalized in {"queued", "claimed", "running", "unknown"}:
        return "warn"
    if normalized in TERMINAL_PROBLEM_STATUSES:
        return "bad"
    return "muted"


def _latest(items: list[dict[str, Any]], *keys: str) -> dict[str, Any] | None:
    if not items:
        return None

    def sort_key(item: dict[str, Any]) -> str:
        for key in keys:
            value = item.get(key)
            if value:
                return str(value)
        return ""

    return sorted(items, key=sort_key)[-1]


def _summarize_adapters(dispatches: list[dict[str, Any]], reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agents = sorted({str(item.get("agent", "unknown")) for item in dispatches if item.get("agent")})
    summaries: list[dict[str, Any]] = []
    for agent in agents:
        agent_dispatches = [item for item in dispatches if item.get("agent") == agent]
        agent_reports = [item for item in reports if item.get("agent") == agent]
        latest_dispatch = _latest(agent_dispatches, "completed_at", "claimed_at", "created_at") or {}
        latest_report = _latest(agent_reports, "_artifact_path") or {}
        stdout_payload = _parse_claude_stdout(latest_report)
        status_counts: dict[str, int] = {}
        for dispatch in agent_dispatches:
            status = str(dispatch.get("status", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1

        observed_cost = stdout_payload.get("total_cost_usd")
        max_budget = latest_report.get("max_budget_usd")
        remaining_budget = None
        if isinstance(observed_cost, (int, float)) and isinstance(max_budget, (int, float)):
            remaining_budget = max(float(max_budget) - float(observed_cost), 0.0)

        problem = ""
        latest_status = str(latest_dispatch.get("status", "unknown"))
        if latest_status in TERMINAL_PROBLEM_STATUSES:
            completion = latest_dispatch.get("completion") or {}
            problem = str(completion.get("error") or completion.get("summary") or latest_report.get("summary") or latest_status)
        elif latest_report.get("success") is False:
            problem = str(latest_report.get("summary", "adapter execution failed"))

        readiness = "READY_SUPERVISED"
        if any(status in status_counts for status in TERMINAL_PROBLEM_STATUSES):
            readiness = "NEEDS_ATTENTION"
        elif status_counts.get("claimed") or status_counts.get("queued"):
            readiness = "WORK_PENDING"

        summaries.append(
            {
                "agent": agent,
                "readiness": readiness,
                "status_counts": status_counts,
                "latest_dispatch": latest_dispatch,
                "latest_report": latest_report,
                "stdout_payload": stdout_payload,
                "observed_cost": observed_cost,
                "max_budget": max_budget,
                "remaining_budget": remaining_budget,
                "problem": problem,
            }
        )
    return summaries


def _html_list(items: list[str], empty: str) -> str:
    if not items:
        return f"<li>{html.escape(empty)}</li>"
    return "\n".join(f"<li>{item}</li>" for item in items)


def _render_matrix_rows(matrix: dict[str, Any]) -> str:
    rows = []
    for item in matrix.get("agents", []):
        blockers = item.get("promotion_blockers") or []
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(str(item.get('agent', 'unknown')))}</strong><br><span>{html.escape(str(item.get('adapter_type', 'unknown')))}</span></td>"
            f"<td><span class=\"pill {_status_class(str(item.get('readiness', 'unknown')))}\">{html.escape(str(item.get('readiness', 'unknown')))}</span></td>"
            f"<td>{html.escape(str(item.get('non_interactive')))}</td>"
            f"<td>{html.escape(str(item.get('supervised')))}</td>"
            f"<td>{html.escape(str(item.get('quota_status', 'unknown')))}<br><span>budget cap: {html.escape(str(item.get('per_run_budget_cap')))}</span></td>"
            f"<td>{html.escape(str(item.get('smoke_gate')))}</td>"
            f"<td>{html.escape('; '.join(blockers) if blockers else 'none')}</td>"
            "</tr>"
        )
    return "".join(rows)


def _render_gate_rows(dispatches: list[dict[str, Any]]) -> str:
    rows = []
    for item in dispatches:
        gate = item.get("gate") or (item.get("completion") or {}).get("gate") or {}
        if not gate:
            continue
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(str(item.get('dispatch_id', 'dispatch')))}</strong><br><span>{html.escape(str(item.get('title', '')))}</span></td>"
            f"<td>{html.escape(str(item.get('agent', 'unknown')))}</td>"
            f"<td><span class=\"pill {_status_class(str(item.get('status', 'unknown')))}\">{html.escape(str(item.get('status', 'unknown')))}</span></td>"
            f"<td>{html.escape(str(gate.get('readiness', 'unknown')))}</td>"
            f"<td>{html.escape(str(gate.get('reason', '')))}</td>"
            "</tr>"
        )
    if not rows:
        return "<tr><td colspan=\"5\">No readiness-gated dispatches yet. Auto-dispatch callers should use <code>--require-ready</code>.</td></tr>"
    return "".join(rows)


def render_dashboard(config: WorkspaceConfig, task_id: str) -> Path:
    task_dir = config.tasks_dir / task_id
    task_json = task_dir / "task.json"
    ledger_json = task_dir / "RUN_LEDGER.json"
    if not task_json.exists():
        raise FileNotFoundError(f"task not found: {task_id}")

    task = _read_json(task_json)
    ledger = _read_json(ledger_json) if ledger_json.exists() else {}
    events = ledger.get("events", [])
    artifacts = ledger.get("artifacts", [])
    dispatches = []
    dispatch_dir = task_dir / "dispatch" / "dispatches"
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.json")):
            dispatches.append(_read_json(path))
    reports = _load_artifact_reports(artifacts)
    usage_snapshot = _read_json(task_dir / "USAGE_SNAPSHOT.json")
    adapter_matrix = build_adapter_matrix(include_doctor=False)
    adapters = _summarize_adapters(dispatches, reports)
    problem_dispatches = [item for item in dispatches if item.get("status") in TERMINAL_PROBLEM_STATUSES]
    pending_dispatches = [item for item in dispatches if item.get("status") in {"queued", "claimed"}]
    completed_dispatches = [item for item in dispatches if item.get("status") == "completed"]
    latest_event = events[-1] if events else {}

    control_cards = "\n".join(
        [
            f"<div class=\"metric\"><span>Task status</span><strong>{html.escape(task.get('status', 'unknown'))}</strong></div>",
            f"<div class=\"metric\"><span>Dispatches</span><strong>{len(completed_dispatches)}/{len(dispatches)} done</strong></div>",
            f"<div class=\"metric\"><span>Artifacts</span><strong>{len(artifacts)}</strong></div>",
            f"<div class=\"metric {_status_class('failed' if problem_dispatches else 'completed')}\"><span>Owner action</span><strong>{'Required' if problem_dispatches else 'None'}</strong></div>",
        ]
    )

    adapter_rows = "\n".join(
        f"""
        <article class="adapter-card">
          <div class="adapter-head">
            <div>
              <div class="label">Adapter</div>
              <h3>{html.escape(adapter['agent'])}</h3>
            </div>
            <span class="pill {_status_class(adapter['readiness'])}">{html.escape(adapter['readiness'])}</span>
          </div>
          <div class="adapter-grid">
            <div><span>Latest dispatch</span><strong>{html.escape(adapter['latest_dispatch'].get('title', 'n/a'))}</strong></div>
            <div><span>Status</span><strong>{html.escape(adapter['latest_dispatch'].get('status', 'unknown'))}</strong></div>
            <div><span>Budget</span><strong>{_display_money(adapter['observed_cost'])} / {_display_money(adapter['max_budget'])}</strong></div>
            <div><span>Remaining</span><strong>{_display_money(adapter['remaining_budget'])}</strong></div>
          </div>
          <p>{html.escape(adapter['latest_report'].get('summary', adapter['problem'] or 'No execution report yet.'))}</p>
          <p class="small">Counts: {html.escape(json.dumps(adapter['status_counts'], sort_keys=True))}</p>
          <p class="small">Transcript: <code>{html.escape(adapter['latest_report'].get('_artifact_label', 'n/a'))}</code></p>
        </article>
        """
        for adapter in adapters
    )
    if not adapter_rows:
        adapter_rows = "<p>No adapter dispatches have been queued yet.</p>"

    usage_rows = ""
    for item in usage_snapshot.get("agents", []):
        usage_rows += (
            "<tr>"
            f"<td>{html.escape(str(item.get('agent', 'unknown')))}</td>"
            f"<td><span class=\"pill {_status_class(str(item.get('quota_status', 'unknown')))}\">{html.escape(str(item.get('quota_status', 'unknown')))}</span></td>"
            f"<td>{html.escape(str(item.get('dispatch_count', 0)))}</td>"
            f"<td>{_display_money(item.get('observed_cost_usd_total'))}</td>"
            f"<td>{_display_money(item.get('max_budget_usd_total'))}</td>"
            f"<td>{_display_money(item.get('budget_remaining_usd_estimate'))}</td>"
            f"<td>{html.escape(str(item.get('last_error') or ''))}</td>"
            "</tr>"
        )
    if not usage_rows:
        usage_rows = "<tr><td colspan=\"7\">No usage snapshot has been generated yet. Run <code>mco usage snapshot &lt;task_id&gt;</code>.</td></tr>"

    escalation_items = []
    for dispatch in problem_dispatches:
        completion = dispatch.get("completion") or {}
        reason = completion.get("error") or completion.get("summary") or "No reason recorded"
        escalation_items.append(
            f"<strong>{html.escape(dispatch.get('dispatch_id', 'dispatch'))}</strong> "
            f"<span class=\"pill bad\">{html.escape(dispatch.get('status', 'unknown'))}</span>"
            f"<p>{html.escape(dispatch.get('agent', 'unknown'))}: {html.escape(str(reason))}</p>"
        )
    for adapter in adapters:
        if adapter["latest_report"].get("success") is False and adapter["problem"]:
            escalation_items.append(
                f"<strong>{html.escape(adapter['agent'])} execution report</strong> "
                f"<span class=\"pill bad\">failed</span><p>{html.escape(adapter['problem'])}</p>"
            )
    if not escalation_items and pending_dispatches:
        escalation_items.append(
            f"<strong>Pending work</strong> <span class=\"pill warn\">watch</span>"
            f"<p>{len(pending_dispatches)} dispatch(es) are queued or claimed. No owner decision is required yet.</p>"
        )
    rows = "\n".join(
        f"<li><strong>{html.escape(event.get('type', 'event'))}</strong> "
        f"<span>{html.escape(event.get('at', ''))}</span><p>{html.escape(event.get('message', ''))}</p></li>"
        for event in events
    )
    artifact_rows = "\n".join(
        f"<li><code>{html.escape(str(item.get('label', 'artifact')))}</code>"
        f"<p>{html.escape(str(item.get('path', item)))}</p></li>"
        if isinstance(item, dict)
        else f"<li><p>{html.escape(str(item))}</p></li>"
        for item in artifacts
    )
    dispatch_rows = "\n".join(
        f"<li><strong>{html.escape(item.get('dispatch_id', 'dispatch'))}</strong> "
        f"<span>{html.escape(item.get('status', 'unknown'))}</span>"
        f"<p>{html.escape(item.get('agent', ''))}: {html.escape(item.get('title', ''))}</p></li>"
        for item in dispatches
    )
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Multi-CLI Orchestrator Dashboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #0f172a; color: #e5e7eb; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px; }}
    header {{ margin-bottom: 24px; }}
    .card, .adapter-card {{ background: #111827; border: 1px solid #263247; border-radius: 14px; padding: 20px; margin-bottom: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.22); }}
    .label {{ color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    h3 {{ margin: 4px 0 0; font-size: 20px; }}
    code {{ background: #1f2937; color: #d1d5db; padding: 2px 5px; border-radius: 5px; }}
    table {{ width: 100%; border-collapse: collapse; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #263247; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .metric {{ background: #0b1220; border: 1px solid #263247; border-radius: 12px; padding: 16px; }}
    .metric span, .adapter-grid span {{ display: block; color: #94a3b8; font-size: 12px; margin-bottom: 6px; }}
    .metric strong, .adapter-grid strong {{ color: #f8fafc; }}
    .adapter-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }}
    .adapter-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
    .adapter-grid div {{ background: #0b1220; border-radius: 10px; padding: 12px; }}
    .pill {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 9px; font-size: 12px; font-weight: 700; }}
    .ok {{ color: #34d399; background: rgba(52,211,153,.12); border-color: rgba(52,211,153,.35); }}
    .warn {{ color: #fbbf24; background: rgba(251,191,36,.12); border-color: rgba(251,191,36,.35); }}
    .bad {{ color: #fb7185; background: rgba(251,113,133,.12); border-color: rgba(251,113,133,.35); }}
    .muted {{ color: #94a3b8; background: rgba(148,163,184,.12); border-color: rgba(148,163,184,.35); }}
    .small {{ color: #94a3b8; font-size: 13px; word-break: break-word; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 12px; }}
    li p {{ margin: 4px 0 0; color: #94a3b8; }}
    @media (max-width: 760px) {{
      .metrics, .adapter-grid {{ grid-template-columns: 1fr 1fr; }}
      main {{ padding: 20px 12px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="label">Boss Dashboard Control Room</div>
    <h1>{html.escape(task.get("title", task_id))}</h1>
    <div>Task: <code>{html.escape(task_id)}</code></div>
  </header>
  <section class="card">
    <h2>Control Room</h2>
    <div class="metrics">{control_cards}</div>
    <p class="label">Generated {html.escape(datetime.now(timezone.utc).isoformat())}</p>
  </section>
  <section class="card">
    <h2>Adapter Readiness</h2>
    {adapter_rows}
  </section>
  <section class="card">
    <h2>Adapter Matrix</h2>
    <p class="small">Policy baseline without provider probing. Run <code>mco adapter matrix --doctor</code> for local doctor status.</p>
    <table>
      <thead>
        <tr><th>Agent</th><th>Readiness</th><th>Non-interactive</th><th>Supervised</th><th>Quota</th><th>Smoke</th><th>Promotion blockers</th></tr>
      </thead>
      <tbody>{_render_matrix_rows(adapter_matrix)}</tbody>
    </table>
  </section>
  <section class="card">
    <h2>Dispatch Gate Status</h2>
    <p class="small">Only dispatches queued with <code>--require-ready</code> include gate evidence.</p>
    <table>
      <thead>
        <tr><th>Dispatch</th><th>Agent</th><th>Status</th><th>Readiness</th><th>Reason</th></tr>
      </thead>
      <tbody>{_render_gate_rows(dispatches)}</tbody>
    </table>
  </section>
  <section class="card">
    <h2>Owner Escalations</h2>
    <ul>{_html_list(escalation_items, "No owner action required.")}</ul>
  </section>
  <section class="card">
    <h2>Usage Snapshot</h2>
    <p class="small">Source: {html.escape(usage_snapshot.get("source", "not generated"))}</p>
    <table>
      <thead>
        <tr><th>Agent</th><th>Quota status</th><th>Dispatches</th><th>Observed</th><th>Budget</th><th>Remaining</th><th>Last error</th></tr>
      </thead>
      <tbody>{usage_rows}</tbody>
    </table>
  </section>
  <section class="card">
    <h2>Current Evidence</h2>
    <p>Latest event: <strong>{html.escape(latest_event.get("type", "none"))}</strong> {html.escape(latest_event.get("message", ""))}</p>
  </section>
  <section class="card">
    <h2>Artifacts</h2>
    <ul>{artifact_rows}</ul>
  </section>
  <section class="card">
    <h2>Dispatches</h2>
    <ul>{dispatch_rows}</ul>
  </section>
  <section class="card">
    <h2>Timeline</h2>
    <ul>{rows}</ul>
  </section>
</main>
</body>
</html>
"""
    out = task_dir / "dashboard.html"
    out.write_text(content, encoding="utf-8")
    return out
