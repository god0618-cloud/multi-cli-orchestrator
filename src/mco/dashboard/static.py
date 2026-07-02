from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mco.adapters.matrix import build_adapter_matrix
from mco.config import WorkspaceConfig
from mco.workflow.engine import observe_workflow


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
    if normalized in {"advance", "complete", "completed", "ready", "ready_supervised", "pass"}:
        return "ok"
    if normalized in {"queued", "claimed", "running", "unknown", "wait"}:
        return "warn"
    if normalized in TERMINAL_PROBLEM_STATUSES or normalized == "escalate":
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
            f"<td>{html.escape(str(item.get('execution_mode', 'unknown')))}<br><span>{html.escape(str(item.get('automation_posture', 'unknown')))}</span></td>"
            f"<td>{html.escape(str(item.get('non_interactive')))}</td>"
            f"<td>{html.escape(str(item.get('supervised')))}</td>"
            f"<td>{html.escape(str(item.get('quota_status', 'unknown')))}<br><span>budget cap: {html.escape(str(item.get('per_run_budget_cap')))}</span></td>"
            f"<td>{html.escape(str(item.get('smoke_gate')))}</td>"
            f"<td>{html.escape(str(item.get('recommended_use', 'unknown')))}<br><span>{html.escape('; '.join(blockers) if blockers else 'none')}</span></td>"
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


def _workflow_observation(task_dir: Path) -> dict[str, Any]:
    if not (task_dir / "plan.json").exists():
        return {
            "schema": "mco.workflow_observe.v1.0",
            "workflow": "none",
            "status": "not_initialized",
            "current_phase": None,
            "recommended_action": "wait",
            "reason": "workflow plan not initialized",
            "dispatch_counts": {},
            "gate_results": [],
        }
    return observe_workflow(task_dir)


def _owner_brief(
    workflow_observation: dict[str, Any],
    problem_dispatches: list[dict[str, Any]],
    pending_dispatches: list[dict[str, Any]],
    task_id: str,
) -> dict[str, str]:
    action = str(workflow_observation.get("recommended_action", "wait"))
    phase = str(workflow_observation.get("current_phase") or "n/a")
    reason = str(workflow_observation.get("reason") or "No workflow reason recorded.")

    if problem_dispatches:
        return {
            "status": "Decision required",
            "class": "bad",
            "headline": "A dispatch is blocked or failed.",
            "detail": "Review Owner Escalations before advancing the workflow.",
            "next_command": f"mco workflow observe {task_id}",
        }
    if pending_dispatches:
        return {
            "status": "Work in progress",
            "class": "warn",
            "headline": f"{len(pending_dispatches)} dispatch(es) are queued or claimed.",
            "detail": "No owner decision is required yet. Watch for terminal status or timeout.",
            "next_command": f"mco status {task_id}",
        }
    if action == "complete":
        return {
            "status": "Ready to close",
            "class": "ok",
            "headline": "Workflow gates are complete.",
            "detail": "Review the close evidence and replay ledger before publishing broader claims.",
            "next_command": f"mco run replay <task-dir>/RUN_LEDGER.json",
        }
    if action == "advance":
        return {
            "status": "Advance available",
            "class": "ok",
            "headline": f"Current phase {phase} can advance.",
            "detail": reason,
            "next_command": f"mco workflow loop {task_id} --max-steps 1",
        }
    if action == "escalate":
        return {
            "status": "Review required",
            "class": "bad",
            "headline": f"Workflow is blocked at {phase}.",
            "detail": reason,
            "next_command": f"mco workflow observe {task_id}",
        }
    return {
        "status": "Waiting",
        "class": "warn",
        "headline": f"Workflow is waiting at {phase}.",
        "detail": reason,
        "next_command": f"mco workflow observe {task_id}",
    }


def _language_script(owner_brief: dict[str, str], workflow_observation: dict[str, Any]) -> str:
    phase = str(workflow_observation.get("current_phase") or "n/a")
    action = str(workflow_observation.get("recommended_action", "wait"))
    owner_brief_zh = {
        "Decision required": {
            "status": "需要决策",
            "headline": "有一个派发任务已阻塞或失败。",
            "detail": "继续推进前，先查看 Owner Escalations。",
        },
        "Work in progress": {
            "status": "执行中",
            "headline": "已有任务正在排队或执行。",
            "detail": "当前不需要老板拍板。继续观察终态或超时即可。",
        },
        "Ready to close": {
            "status": "可收口",
            "headline": "工作流门禁已完成。",
            "detail": "对外声明前，先复核 close evidence 和 replay ledger。",
        },
        "Advance available": {
            "status": "可推进",
            "headline": f"当前阶段 {phase} 可以推进。",
            "detail": str(workflow_observation.get("reason") or owner_brief.get("detail", "")),
        },
        "Review required": {
            "status": "需要复核",
            "headline": f"工作流在 {phase} 阶段阻塞。",
            "detail": str(workflow_observation.get("reason") or owner_brief.get("detail", "")),
        },
        "Waiting": {
            "status": "等待中",
            "headline": f"工作流正在 {phase} 阶段等待。",
            "detail": str(workflow_observation.get("reason") or owner_brief.get("detail", "")),
        },
    }.get(owner_brief.get("status", ""), {})

    dictionary = {
        "en": {
            "boss_dashboard_control_room": "Boss Dashboard Control Room",
            "task": "Task",
            "operator_brief": "Operator Brief",
            "next_command": "Next Command",
            "hint_disclaimer": "This is a hint, not automatic authority. Use workflow gates and evidence before advancing.",
            "control_room": "Control Room",
            "generated": "Generated",
            "workflow_loop_control": "Workflow Loop Control",
            "workflow": "Workflow",
            "current_phase": "Current phase",
            "recommended_action": "Recommended action",
            "reason": "Reason",
            "gate": "Gate",
            "status": "Status",
            "detail": "Detail",
            "adapter_readiness": "Adapter Readiness",
            "adapter": "Adapter",
            "latest_dispatch": "Latest dispatch",
            "budget": "Budget",
            "remaining": "Remaining",
            "adapter_matrix": "Adapter Matrix",
            "matrix_hint": "Policy baseline without provider probing. Run <code>mco adapter matrix --doctor</code> for local doctor status.",
            "agent": "Agent",
            "readiness": "Readiness",
            "execution_mode": "Execution mode",
            "non_interactive": "Non-interactive",
            "supervised": "Supervised",
            "quota": "Quota",
            "smoke": "Smoke",
            "use_blockers": "Use / blockers",
            "dispatch_gate_status": "Dispatch Gate Status",
            "dispatch_gate_hint": "Only dispatches queued with <code>--require-ready</code> include gate evidence.",
            "dispatch": "Dispatch",
            "owner_escalations": "Owner Escalations",
            "usage_snapshot": "Usage Snapshot",
            "quota_status": "Quota status",
            "dispatches": "Dispatches",
            "observed": "Observed",
            "last_error": "Last error",
            "current_evidence": "Current Evidence",
            "latest_event": "Latest event",
            "artifacts": "Artifacts",
            "timeline": "Timeline",
            "task_status": "Task status",
            "owner_action": "Owner action",
            "workflow_action": "Workflow action",
            "done": "done",
            "required": "Required",
            "none": "None",
            "language_toggle": "中文",
            "language_label": "Language",
            "brief_status": owner_brief.get("status", ""),
            "brief_headline": owner_brief.get("headline", ""),
            "brief_detail": owner_brief.get("detail", ""),
        },
        "zh": {
            "boss_dashboard_control_room": "老板视角控制室",
            "task": "任务",
            "operator_brief": "操作摘要",
            "next_command": "下一条建议命令",
            "hint_disclaimer": "这是提示，不是自动授权。推进前仍需以工作流门禁和证据为准。",
            "control_room": "控制室",
            "generated": "生成时间",
            "workflow_loop_control": "工作流循环控制",
            "workflow": "工作流",
            "current_phase": "当前阶段",
            "recommended_action": "建议动作",
            "reason": "原因",
            "gate": "门禁",
            "status": "状态",
            "detail": "详情",
            "adapter_readiness": "适配器就绪度",
            "adapter": "适配器",
            "latest_dispatch": "最近派发",
            "budget": "预算",
            "remaining": "剩余",
            "adapter_matrix": "适配器矩阵",
            "matrix_hint": "不探测供应商的策略基线。本机 doctor 状态请运行 <code>mco adapter matrix --doctor</code>。",
            "agent": "Agent",
            "readiness": "就绪度",
            "execution_mode": "执行模式",
            "non_interactive": "非交互",
            "supervised": "受监管",
            "quota": "额度",
            "smoke": "冒烟",
            "use_blockers": "用途 / 阻断",
            "dispatch_gate_status": "派发门禁状态",
            "dispatch_gate_hint": "只有通过 <code>--require-ready</code> 排队的派发任务才包含门禁证据。",
            "dispatch": "派发",
            "owner_escalations": "老板拍板事项",
            "usage_snapshot": "用量快照",
            "quota_status": "额度状态",
            "dispatches": "派发数",
            "observed": "已观测",
            "last_error": "最近错误",
            "current_evidence": "当前证据",
            "latest_event": "最近事件",
            "artifacts": "产物",
            "timeline": "时间线",
            "task_status": "任务状态",
            "owner_action": "老板动作",
            "workflow_action": "工作流动作",
            "done": "完成",
            "required": "需要",
            "none": "无",
            "language_toggle": "English",
            "language_label": "语言",
            "brief_status": owner_brief_zh.get("status", owner_brief.get("status", "")),
            "brief_headline": owner_brief_zh.get("headline", owner_brief.get("headline", "")),
            "brief_detail": owner_brief_zh.get("detail", owner_brief.get("detail", "")),
        },
    }
    dynamic = {
        "recommended_action": action,
    }
    payload = json.dumps({"dictionary": dictionary, "dynamic": dynamic}, ensure_ascii=False)
    return f"""
  <script>
    const MCO_DASHBOARD_I18N = {payload};
    function setDashboardLanguage(lang) {{
      const nextLang = lang === "zh" ? "zh" : "en";
      const dict = MCO_DASHBOARD_I18N.dictionary[nextLang];
      document.documentElement.lang = nextLang === "zh" ? "zh-CN" : "en";
      document.querySelectorAll("[data-i18n]").forEach((node) => {{
        const key = node.getAttribute("data-i18n");
        if (dict[key] !== undefined) {{
          node.innerHTML = dict[key];
        }}
      }});
      document.querySelectorAll("[data-i18n-title]").forEach((node) => {{
        const key = node.getAttribute("data-i18n-title");
        if (dict[key] !== undefined) {{
          node.setAttribute("title", dict[key]);
          node.setAttribute("aria-label", dict[key]);
        }}
      }});
      localStorage.setItem("mco.dashboard.language", nextLang);
    }}
    document.addEventListener("DOMContentLoaded", () => {{
      const stored = localStorage.getItem("mco.dashboard.language");
      setDashboardLanguage(stored || "en");
      document.querySelector("[data-language-toggle]")?.addEventListener("click", () => {{
        const current = document.documentElement.lang === "zh-CN" ? "zh" : "en";
        setDashboardLanguage(current === "zh" ? "en" : "zh");
      }});
    }});
  </script>
"""


def _render_workflow_gate_rows(observation: dict[str, Any]) -> str:
    rows = []
    for item in observation.get("gate_results", []):
        status = "pass" if item.get("ok") else "blocked"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('gate', 'gate')))}</td>"
            f"<td><span class=\"pill {_status_class(status)}\">{html.escape(status)}</span></td>"
            f"<td>{html.escape(str(item.get('detail', '')))}</td>"
            "</tr>"
        )
    if not rows:
        return "<tr><td colspan=\"3\">No current gate details. The workflow may be waiting on dispatches, completed, or not initialized.</td></tr>"
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
    workflow_observation = _workflow_observation(task_dir)
    adapters = _summarize_adapters(dispatches, reports)
    problem_dispatches = [item for item in dispatches if item.get("status") in TERMINAL_PROBLEM_STATUSES]
    pending_dispatches = [item for item in dispatches if item.get("status") in {"queued", "claimed"}]
    completed_dispatches = [item for item in dispatches if item.get("status") == "completed"]
    latest_event = events[-1] if events else {}
    owner_brief = _owner_brief(workflow_observation, problem_dispatches, pending_dispatches, task_id)

    control_cards = "\n".join(
        [
            f"<div class=\"metric\"><span data-i18n=\"task_status\">Task status</span><strong>{html.escape(task.get('status', 'unknown'))}</strong></div>",
            f"<div class=\"metric\"><span data-i18n=\"dispatches\">Dispatches</span><strong>{len(completed_dispatches)}/{len(dispatches)} <span data-i18n=\"done\">done</span></strong></div>",
            f"<div class=\"metric\"><span data-i18n=\"artifacts\">Artifacts</span><strong>{len(artifacts)}</strong></div>",
            f"<div class=\"metric {_status_class('failed' if problem_dispatches else 'completed')}\"><span data-i18n=\"owner_action\">Owner action</span><strong data-i18n=\"{'required' if problem_dispatches else 'none'}\">{'Required' if problem_dispatches else 'None'}</strong></div>",
            f"<div class=\"metric {_status_class(str(workflow_observation.get('recommended_action', 'wait')))}\"><span data-i18n=\"workflow_action\">Workflow action</span><strong>{html.escape(str(workflow_observation.get('recommended_action', 'wait')))}</strong></div>",
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
            <div><span data-i18n="latest_dispatch">Latest dispatch</span><strong>{html.escape(adapter['latest_dispatch'].get('title', 'n/a'))}</strong></div>
            <div><span data-i18n="status">Status</span><strong>{html.escape(adapter['latest_dispatch'].get('status', 'unknown'))}</strong></div>
            <div><span data-i18n="budget">Budget</span><strong>{_display_money(adapter['observed_cost'])} / {_display_money(adapter['max_budget'])}</strong></div>
            <div><span data-i18n="remaining">Remaining</span><strong>{_display_money(adapter['remaining_budget'])}</strong></div>
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
    .brief {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(260px, .8fr); gap: 16px; align-items: stretch; }}
    .brief-panel {{ background: #0b1220; border: 1px solid #263247; border-radius: 12px; padding: 18px; }}
    .brief-panel h2 {{ margin-bottom: 6px; font-size: 24px; }}
    .brief-panel p {{ color: #94a3b8; margin: 8px 0 0; }}
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
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .lang-toggle {{ background: #1f2937; color: #f8fafc; border: 1px solid #334155; border-radius: 999px; padding: 8px 12px; font-weight: 700; cursor: pointer; }}
    .lang-toggle:hover {{ border-color: #60a5fa; color: #bfdbfe; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 12px; }}
    li p {{ margin: 4px 0 0; color: #94a3b8; }}
    @media (max-width: 760px) {{
      .metrics, .adapter-grid, .brief {{ grid-template-columns: 1fr; }}
      main {{ padding: 20px 12px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="topbar">
      <div>
        <div class="label" data-i18n="boss_dashboard_control_room">Boss Dashboard Control Room</div>
        <h1>{html.escape(task.get("title", task_id))}</h1>
        <div><span data-i18n="task">Task</span>: <code>{html.escape(task_id)}</code></div>
      </div>
      <button class="lang-toggle" type="button" data-language-toggle data-i18n="language_toggle" data-i18n-title="language_label" title="Language" aria-label="Language">中文</button>
    </div>
  </header>
  <section class="card">
    <div class="brief">
      <div class="brief-panel">
        <div class="label" data-i18n="operator_brief">Operator Brief</div>
        <h2 data-i18n="brief_headline">{html.escape(owner_brief["headline"])}</h2>
        <span class="pill {html.escape(owner_brief["class"])}" data-i18n="brief_status">{html.escape(owner_brief["status"])}</span>
        <p data-i18n="brief_detail">{html.escape(owner_brief["detail"])}</p>
      </div>
      <div class="brief-panel">
        <div class="label" data-i18n="next_command">Next Command</div>
        <p><code>{html.escape(owner_brief["next_command"])}</code></p>
        <p class="small" data-i18n="hint_disclaimer">This is a hint, not automatic authority. Use workflow gates and evidence before advancing.</p>
      </div>
    </div>
  </section>
  <section class="card">
    <h2 data-i18n="control_room">Control Room</h2>
    <div class="metrics">{control_cards}</div>
    <p class="label"><span data-i18n="generated">Generated</span> {html.escape(datetime.now(timezone.utc).isoformat())}</p>
  </section>
  <section class="card">
    <h2 data-i18n="workflow_loop_control">Workflow Loop Control</h2>
    <div class="metrics">
      <div class="metric"><span data-i18n="workflow">Workflow</span><strong>{html.escape(str(workflow_observation.get('workflow', 'none')))}</strong></div>
      <div class="metric"><span data-i18n="current_phase">Current phase</span><strong>{html.escape(str(workflow_observation.get('current_phase') or 'n/a'))}</strong></div>
      <div class="metric {_status_class(str(workflow_observation.get('recommended_action', 'wait')))}"><span data-i18n="recommended_action">Recommended action</span><strong>{html.escape(str(workflow_observation.get('recommended_action', 'wait')))}</strong></div>
      <div class="metric"><span data-i18n="reason">Reason</span><strong>{html.escape(str(workflow_observation.get('reason', '')))}</strong></div>
    </div>
    <table>
      <thead>
        <tr><th data-i18n="gate">Gate</th><th data-i18n="status">Status</th><th data-i18n="detail">Detail</th></tr>
      </thead>
      <tbody>{_render_workflow_gate_rows(workflow_observation)}</tbody>
    </table>
  </section>
  <section class="card">
    <h2 data-i18n="adapter_readiness">Adapter Readiness</h2>
    {adapter_rows}
  </section>
  <section class="card">
    <h2 data-i18n="adapter_matrix">Adapter Matrix</h2>
    <p class="small" data-i18n="matrix_hint">Policy baseline without provider probing. Run <code>mco adapter matrix --doctor</code> for local doctor status.</p>
    <table>
      <thead>
        <tr><th data-i18n="agent">Agent</th><th data-i18n="readiness">Readiness</th><th data-i18n="execution_mode">Execution mode</th><th data-i18n="non_interactive">Non-interactive</th><th data-i18n="supervised">Supervised</th><th data-i18n="quota">Quota</th><th data-i18n="smoke">Smoke</th><th data-i18n="use_blockers">Use / blockers</th></tr>
      </thead>
      <tbody>{_render_matrix_rows(adapter_matrix)}</tbody>
    </table>
  </section>
  <section class="card">
    <h2 data-i18n="dispatch_gate_status">Dispatch Gate Status</h2>
    <p class="small" data-i18n="dispatch_gate_hint">Only dispatches queued with <code>--require-ready</code> include gate evidence.</p>
    <table>
      <thead>
        <tr><th data-i18n="dispatch">Dispatch</th><th data-i18n="agent">Agent</th><th data-i18n="status">Status</th><th data-i18n="readiness">Readiness</th><th data-i18n="reason">Reason</th></tr>
      </thead>
      <tbody>{_render_gate_rows(dispatches)}</tbody>
    </table>
  </section>
  <section class="card">
    <h2 data-i18n="owner_escalations">Owner Escalations</h2>
    <ul>{_html_list(escalation_items, "No owner action required.")}</ul>
  </section>
  <section class="card">
    <h2 data-i18n="usage_snapshot">Usage Snapshot</h2>
    <p class="small">Source: {html.escape(usage_snapshot.get("source", "not generated"))}</p>
    <table>
      <thead>
        <tr><th data-i18n="agent">Agent</th><th data-i18n="quota_status">Quota status</th><th data-i18n="dispatches">Dispatches</th><th data-i18n="observed">Observed</th><th data-i18n="budget">Budget</th><th data-i18n="remaining">Remaining</th><th data-i18n="last_error">Last error</th></tr>
      </thead>
      <tbody>{usage_rows}</tbody>
    </table>
  </section>
  <section class="card">
    <h2 data-i18n="current_evidence">Current Evidence</h2>
    <p><span data-i18n="latest_event">Latest event</span>: <strong>{html.escape(latest_event.get("type", "none"))}</strong> {html.escape(latest_event.get("message", ""))}</p>
  </section>
  <section class="card">
    <h2 data-i18n="artifacts">Artifacts</h2>
    <ul>{artifact_rows}</ul>
  </section>
  <section class="card">
    <h2 data-i18n="dispatches">Dispatches</h2>
    <ul>{dispatch_rows}</ul>
  </section>
  <section class="card">
    <h2 data-i18n="timeline">Timeline</h2>
    <ul>{rows}</ul>
  </section>
</main>
{_language_script(owner_brief, workflow_observation)}
</body>
</html>
"""
    out = task_dir / "dashboard.html"
    out.write_text(content, encoding="utf-8")
    return out
