from __future__ import annotations

import html
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


def render_replay_html(path: Path, output_path: Path) -> Path:
    ledger = read_ledger(path)
    events = ledger.get("events", [])
    artifacts = ledger.get("artifacts", [])
    sandbox_refs = ledger.get("sandbox_contract_refs", [])
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    event_rows = "\n".join(
        "<tr>"
        f"<td>{index}</td>"
        f"<td>{html.escape(str(event.get('at', '-')))}</td>"
        f"<td><code>{html.escape(str(event.get('type', '-')))}</code></td>"
        f"<td>{html.escape(str(event.get('message', '')))}</td>"
        "</tr>"
        for index, event in enumerate(events, start=1)
    )
    if not event_rows:
        event_rows = "<tr><td colspan=\"4\">No events recorded.</td></tr>"

    artifact_items = []
    for artifact in artifacts:
        if isinstance(artifact, dict):
            artifact_items.append(f"<li><strong>{html.escape(str(artifact.get('label', 'artifact')))}</strong>: <code>{html.escape(str(artifact.get('path', '')))}</code></li>")
        else:
            artifact_items.append(f"<li><code>{html.escape(str(artifact))}</code></li>")
    if not artifact_items:
        artifact_items.append("<li>No artifacts recorded.</li>")

    sandbox_items = [f"<li><code>{html.escape(str(ref))}</code></li>" for ref in sandbox_refs] or ["<li>No sandbox contracts recorded.</li>"]

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCO Run Replay</title>
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: #172033; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 56px; }}
    header {{ display: grid; gap: 10px; margin-bottom: 24px; }}
    h1 {{ margin: 0; font-size: 30px; }}
    h2 {{ margin-top: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ background: #fff; border: 1px solid #dce3ef; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(13, 24, 45, 0.04); }}
    .card span {{ display: block; color: #65758b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .card strong {{ display: block; margin-top: 4px; font-size: 15px; word-break: break-word; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #dce3ef; border-radius: 8px; overflow: hidden; }}
    th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #e8edf5; vertical-align: top; }}
    th {{ background: #eef3fa; font-size: 12px; color: #41516a; text-transform: uppercase; letter-spacing: 0.04em; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; }}
    ul {{ background: #fff; border: 1px solid #dce3ef; border-radius: 8px; margin: 0; padding: 14px 14px 14px 32px; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>MCO Run Replay</h1>
      <p>Static replay generated from <code>{html.escape(str(path))}</code>.</p>
    </header>
    <section class="grid">
      <div class="card"><span>Task</span><strong>{html.escape(str(ledger.get('task_id') or '-'))}</strong></div>
      <div class="card"><span>Run</span><strong>{html.escape(str(ledger.get('run_id') or '-'))}</strong></div>
      <div class="card"><span>Workflow</span><strong>{html.escape(str(ledger.get('workflow') or '-'))}</strong></div>
      <div class="card"><span>Final verdict</span><strong>{html.escape(str(ledger.get('final_verdict') or '-'))}</strong></div>
      <div class="card"><span>Events</span><strong>{len(events)}</strong></div>
      <div class="card"><span>Artifacts</span><strong>{len(artifacts)}</strong></div>
    </section>
    <h2>Timeline</h2>
    <table>
      <thead><tr><th>#</th><th>At</th><th>Type</th><th>Message</th></tr></thead>
      <tbody>{event_rows}</tbody>
    </table>
    <h2>Artifacts</h2>
    <ul>{''.join(artifact_items)}</ul>
    <h2>Sandbox Contracts</h2>
    <ul>{''.join(sandbox_items)}</ul>
  </main>
</body>
</html>
"""
    output_path.write_text(document, encoding="utf-8")
    return output_path
