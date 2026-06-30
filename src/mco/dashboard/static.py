from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from mco.config import WorkspaceConfig


def render_dashboard(config: WorkspaceConfig, task_id: str) -> Path:
    task_dir = config.tasks_dir / task_id
    task_json = task_dir / "task.json"
    ledger_json = task_dir / "RUN_LEDGER.json"
    if not task_json.exists():
        raise FileNotFoundError(f"task not found: {task_id}")

    task = json.loads(task_json.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_json.read_text(encoding="utf-8")) if ledger_json.exists() else {}
    events = ledger.get("events", [])
    artifacts = ledger.get("artifacts", [])
    dispatches = []
    dispatch_dir = task_dir / "dispatch" / "dispatches"
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.json")):
            dispatches.append(json.loads(path.read_text(encoding="utf-8")))
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
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f8fa; color: #1f2937; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 32px 20px; }}
    header {{ margin-bottom: 24px; }}
    .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
    .label {{ color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 5px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 12px; }}
    li p {{ margin: 4px 0 0; color: #4b5563; }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="label">Boss Dashboard Seed</div>
    <h1>{html.escape(task.get("title", task_id))}</h1>
    <div>Task: <code>{html.escape(task_id)}</code></div>
  </header>
  <section class="card">
    <h2>Status</h2>
    <p>{html.escape(task.get("status", "unknown"))}</p>
    <p class="label">Generated {html.escape(datetime.now(timezone.utc).isoformat())}</p>
  </section>
  <section class="card">
    <h2>Current Evidence</h2>
    <p>Loop spec and run ledger exist. Registered artifacts are listed below.</p>
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
