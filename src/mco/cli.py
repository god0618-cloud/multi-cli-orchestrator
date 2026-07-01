from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from .adapters.doctor import doctor_adapter, manifest_for_agent
from .adapters.matrix import build_adapter_matrix, write_adapter_matrix
from .adapters.scaffold import scaffold_adapter
from .adapters.smoke import smoke_claude_code, smoke_kimi_code
from .audit.safety import audit_tree
from .config import init_workspace, read_workspace_config, resolve_workspace
from .dashboard.static import render_dashboard
from .demo.hello import run_hello_demo
from .demo.walkthrough import run_walkthrough_demo
from .dispatch.queue import claim_dispatch, complete_dispatch, list_dispatches, queue_dispatch
from .dispatch.execute import execute_dispatch_claude_prompt, execute_dispatch_command, execute_dispatch_dry_run, execute_dispatch_kimi_prompt
from .monitor import run_monitor
from .replay.ledger import append_event, register_artifact, set_workflow
from .replay.readout import replay_ledger
from .release.check import check_release
from .schemas import (
    default_loop_spec,
    default_run_ledger,
    validate_loop_spec,
    validate_adapter_manifest,
    validate_run_ledger,
    validate_sandbox_contract,
)
from .status import build_status_snapshot, render_status_text
from .task.lifecycle import create_task, list_tasks, read_task, task_dir
from .usage.snapshot import write_usage_snapshot
from .workflow.templates import load_workflow_template, write_plan
from .workflow.engine import advance_workflow, workflow_status


def cmd_init(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    init_workspace(config)

    loop_path = config.config_dir / "LOOP_SPEC.template.json"
    if not loop_path.exists():
        loop_path.write_text(json.dumps(default_loop_spec(), indent=2) + "\n", encoding="utf-8")

    ledger_path = config.config_dir / "RUN_LEDGER.template.json"
    if not ledger_path.exists():
        ledger_path.write_text(json.dumps(default_run_ledger(), indent=2) + "\n", encoding="utf-8")

    print(f"initialized workspace: {config.workspace_root}")
    print(f"config: {config.config_path}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    checks = []

    try:
        payload = read_workspace_config(config)
        checks.append(("config", True, payload.get("schema", "unknown")))
    except Exception as exc:
        checks.append(("config", False, str(exc)))

    loop_template = config.config_dir / "LOOP_SPEC.template.json"
    if loop_template.exists():
        try:
            validate_loop_spec(json.loads(loop_template.read_text(encoding="utf-8")))
            checks.append(("loop_spec_template", True, str(loop_template)))
        except Exception as exc:
            checks.append(("loop_spec_template", False, str(exc)))
    else:
        checks.append(("loop_spec_template", False, "missing"))

    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{status} {name}: {detail}")

    return 0 if all(ok for _, ok, _ in checks) else 1


def cmd_task_create(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    created = create_task(config, args.title, args.request)
    if args.json:
        print(
            json.dumps(
                {
                    "task_id": created.task_id,
                    "task_dir": str(created.task_dir),
                    "loop_spec": str(created.loop_spec_path),
                    "run_ledger": str(created.run_ledger_path),
                },
                indent=2,
            )
        )
        return 0
    print(f"created task: {created.task_id}")
    print(f"task_dir: {created.task_dir}")
    print(f"loop_spec: {created.loop_spec_path}")
    print(f"run_ledger: {created.run_ledger_path}")
    return 0


def cmd_task_list(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    for task in list_tasks(config):
        print(f"{task.get('task_id')}\t{task.get('status')}\t{task.get('title')}")
    return 0


def cmd_task_status(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    payload = read_task(config, args.task_id)
    print(json.dumps(payload, indent=2))
    return 0


def cmd_task_event(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    event = append_event(directory, args.type, args.message)
    print(json.dumps(event, indent=2))
    return 0


def cmd_artifact_register(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    artifact_path = Path(args.path).expanduser().resolve()
    if not artifact_path.exists():
        raise FileNotFoundError(f"artifact not found: {artifact_path}")
    artifact = register_artifact(directory, artifact_path, args.label)
    print(json.dumps(artifact, indent=2))
    return 0


def cmd_adapter_capabilities(args: argparse.Namespace) -> int:
    print(json.dumps(manifest_for_agent(args.agent), indent=2))
    return 0


def cmd_adapter_doctor(args: argparse.Namespace) -> int:
    sandbox_path = Path(args.sandbox).expanduser().resolve() if args.sandbox else None
    result = doctor_adapter(args.agent, sandbox_path)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status in {"READY_SUPERVISED", "READY_MANUAL"} else 1


def cmd_adapter_smoke(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    if args.agent == "claude-code":
        result = smoke_claude_code(
            config,
            max_budget_usd=args.max_budget_usd,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    elif args.agent == "kimi-code":
        result = smoke_kimi_code(
            config,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    else:
        raise ValueError("adapter smoke currently supports claude-code and kimi-code")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


def cmd_adapter_scaffold(args: argparse.Namespace) -> int:
    result = scaffold_adapter(args.agent, Path(args.output_dir).expanduser().resolve(), force=args.force)
    print(json.dumps(result, indent=2))
    return 0


def cmd_adapter_matrix(args: argparse.Namespace) -> int:
    if args.output:
        result = write_adapter_matrix(
            Path(args.output).expanduser().resolve(),
            Path(args.html).expanduser().resolve() if args.html else None,
            include_doctor=args.doctor,
        )
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(build_adapter_matrix(include_doctor=args.doctor), indent=2))
    return 0


def cmd_dispatch_queue(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    sandbox_path = Path(args.sandbox).expanduser().resolve() if args.sandbox else None
    dispatch = queue_dispatch(
        directory,
        args.agent,
        args.title,
        args.instructions,
        require_ready=args.require_ready,
        sandbox_path=sandbox_path,
    )
    print(json.dumps(dispatch, indent=2))
    return 1 if args.require_ready and dispatch["status"] == "blocked" else 0


def cmd_dispatch_list(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    for dispatch in list_dispatches(directory):
        print(f"{dispatch.get('dispatch_id')}\t{dispatch.get('agent')}\t{dispatch.get('status')}\t{dispatch.get('title')}")
    return 0


def cmd_dispatch_claim(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    dispatch = claim_dispatch(directory, args.dispatch_id, args.agent)
    print(json.dumps(dispatch, indent=2))
    return 0


def cmd_dispatch_complete(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    dispatch = complete_dispatch(directory, args.dispatch_id, args.agent, args.summary)
    print(json.dumps(dispatch, indent=2))
    return 0


def cmd_dispatch_execute(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    sandbox_path = Path(args.sandbox).expanduser().resolve() if args.sandbox else None
    if args.dry_run:
        dispatch = execute_dispatch_dry_run(directory, args.dispatch_id, args.agent, sandbox_path)
    elif args.agent == "claude-code":
        if not args.prompt_file:
            raise ValueError("--prompt-file is required for claude-code execution")
        dispatch = execute_dispatch_claude_prompt(
            directory,
            args.dispatch_id,
            args.agent,
            sandbox_path,
            Path(args.prompt_file),
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
            max_budget_usd=args.max_budget_usd,
        )
    elif args.agent == "kimi-code":
        if not args.prompt_file:
            raise ValueError("--prompt-file is required for kimi-code execution")
        dispatch = execute_dispatch_kimi_prompt(
            directory,
            args.dispatch_id,
            args.agent,
            sandbox_path,
            Path(args.prompt_file),
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    else:
        if not args.command_json:
            raise ValueError("--command-json is required unless --dry-run is set")
        command = json.loads(args.command_json)
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise ValueError("--command-json must be a JSON string array")
        dispatch = execute_dispatch_command(
            directory,
            args.dispatch_id,
            args.agent,
            sandbox_path,
            command,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    print(json.dumps(dispatch, indent=2))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    out = render_dashboard(config, args.task_id)
    print(f"dashboard: {out}")
    return 0


def cmd_dashboard_serve(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = config.workspace_root
    os.chdir(directory)
    server = ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler)
    print(f"serving {directory} at http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    return 0


def cmd_orchestrate_start(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    template = load_workflow_template(args.template)
    created = create_task(config, args.title, args.request)
    plan_path = write_plan(created.task_dir, template)
    set_workflow(created.task_dir, template["name"])
    append_event(
        created.task_dir,
        "workflow_initialized",
        f"Workflow initialized from template: {template['name']}",
        {"plan": str(plan_path)},
    )
    dashboard_path = render_dashboard(config, created.task_id)
    print(f"created task: {created.task_id}")
    print(f"plan: {plan_path}")
    print(f"dashboard: {dashboard_path}")
    return 0


def cmd_workflow_status(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    print(json.dumps(workflow_status(directory), indent=2))
    return 0


def cmd_workflow_advance(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    result = advance_workflow(
        directory,
        args.phase,
        args.verdict,
        args.summary,
        auto_dispatch=args.auto_dispatch,
        require_ready=args.require_ready,
    )
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "blocked" else 0


def cmd_schema_validate(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
    if args.kind == "loop-spec":
        validate_loop_spec(payload)
    elif args.kind == "adapter-manifest":
        validate_adapter_manifest(payload)
    elif args.kind == "sandbox-contract":
        validate_sandbox_contract(payload)
    elif args.kind == "run-ledger":
        validate_run_ledger(payload)
    else:
        raise ValueError(f"unknown schema kind: {args.kind}")
    print(f"PASS {args.kind}: {args.path}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    result = audit_tree(root)
    print(f"PASS={result.pass_count} WARN={result.warn_count} FAIL={result.fail_count}")
    for finding in result.findings:
        print(f"FAIL {finding}")
    return 0 if result.ok else 1


def cmd_demo_hello(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    result = run_hello_demo(config)
    print(json.dumps(result, indent=2))
    return 0


def cmd_demo_walkthrough(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    result = run_walkthrough_demo(config, Path(args.output_dir))
    print(json.dumps(result, indent=2))
    return 0


def cmd_run_replay(args: argparse.Namespace) -> int:
    path = Path(args.ledger).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"ledger not found: {path}")
    print(replay_ledger(path, json_output=args.json))
    return 0


def cmd_usage_snapshot(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    directory = task_dir(config, args.task_id)
    out = write_usage_snapshot(directory)
    print(f"usage snapshot: {out}")
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    result = check_release(root)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"PASS={result.pass_count} WARN={result.warn_count} FAIL={result.fail_count}")
        for finding in result.findings:
            print(f"{finding['level']} {finding['name']}: {finding['detail']}")
    return 0 if result.ok else 1


def cmd_status(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    snapshot = build_status_snapshot(config, task_id=args.task_id, include_audit=args.audit, include_doctor=args.doctor)
    if args.json:
        print(snapshot.to_json())
    else:
        print(render_status_text(snapshot))
    audit = snapshot.payload.get("audit")
    return 1 if audit is not None and not audit["ok"] else 0


def cmd_monitor(args: argparse.Namespace) -> int:
    config = resolve_workspace(args.workspace)
    read_workspace_config(config)
    result = run_monitor(
        config,
        args.task_id,
        cycles=args.cycles,
        interval_seconds=args.interval_seconds,
        include_audit=args.audit,
        include_doctor=args.doctor,
    )
    print(json.dumps(result, indent=2))
    return int(result["exit_code"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mco", description="Multi-CLI Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize a local MCO workspace")
    p_init.add_argument("--workspace", default=".", help="workspace root")
    p_init.set_defaults(func=cmd_init)

    p_doctor = sub.add_parser("doctor", help="check local MCO workspace readiness")
    p_doctor.add_argument("--workspace", default=".", help="workspace root")
    p_doctor.set_defaults(func=cmd_doctor)

    p_status = sub.add_parser("status", help="show compact operator status for the workspace")
    p_status.add_argument("--workspace", default=".", help="workspace root")
    p_status.add_argument("--task-id", help="task to summarize; defaults to latest task")
    p_status.add_argument("--json", action="store_true", help="print structured JSON")
    p_status.add_argument("--audit", action="store_true", help="include workspace audit counts")
    p_status.add_argument("--doctor", action="store_true", help="probe implemented adapter CLIs and include doctor readiness")
    p_status.set_defaults(func=cmd_status)

    p_monitor = sub.add_parser("monitor", help="write bounded task status snapshots as evidence")
    p_monitor.add_argument("task_id")
    p_monitor.add_argument("--workspace", default=".", help="workspace root")
    p_monitor.add_argument("--cycles", type=int, default=1, help="number of snapshots to write; max 24")
    p_monitor.add_argument("--interval-seconds", type=float, default=0, help="delay between cycles; max 3600")
    p_monitor.add_argument("--audit", action="store_true", help="include workspace audit counts")
    p_monitor.add_argument("--doctor", action="store_true", help="probe implemented adapter CLIs and include doctor readiness")
    p_monitor.set_defaults(func=cmd_monitor)

    p_task = sub.add_parser("task", help="manage tasks")
    task_sub = p_task.add_subparsers(dest="task_command", required=True)

    p_task_create = task_sub.add_parser("create", help="create a task with default loop spec")
    p_task_create.add_argument("title")
    p_task_create.add_argument("--request", help="original user request")
    p_task_create.add_argument("--json", action="store_true", help="print structured JSON")
    p_task_create.add_argument("--workspace", default=".", help="workspace root")
    p_task_create.set_defaults(func=cmd_task_create)

    p_task_list = task_sub.add_parser("list", help="list tasks")
    p_task_list.add_argument("--workspace", default=".", help="workspace root")
    p_task_list.set_defaults(func=cmd_task_list)

    p_task_status = task_sub.add_parser("status", help="show task metadata")
    p_task_status.add_argument("task_id")
    p_task_status.add_argument("--workspace", default=".", help="workspace root")
    p_task_status.set_defaults(func=cmd_task_status)

    p_task_event = task_sub.add_parser("event", help="append a run ledger event")
    p_task_event.add_argument("task_id")
    p_task_event.add_argument("--type", default="note", help="event type")
    p_task_event.add_argument("--message", required=True, help="event message")
    p_task_event.add_argument("--workspace", default=".", help="workspace root")
    p_task_event.set_defaults(func=cmd_task_event)

    p_artifact = sub.add_parser("artifact", help="manage task artifacts")
    artifact_sub = p_artifact.add_subparsers(dest="artifact_command", required=True)

    p_artifact_register = artifact_sub.add_parser("register", help="register an artifact in the run ledger")
    p_artifact_register.add_argument("task_id")
    p_artifact_register.add_argument("path")
    p_artifact_register.add_argument("--label")
    p_artifact_register.add_argument("--workspace", default=".", help="workspace root")
    p_artifact_register.set_defaults(func=cmd_artifact_register)

    p_adapter = sub.add_parser("adapter", help="adapter capability utilities")
    adapter_sub = p_adapter.add_subparsers(dest="adapter_command", required=True)
    p_adapter_cap = adapter_sub.add_parser("capabilities", help="show adapter capability manifest")
    p_adapter_cap.add_argument("agent", choices=["generic-cli", "claude-code", "kimi-code"])
    p_adapter_cap.set_defaults(func=cmd_adapter_capabilities)

    p_adapter_doctor = adapter_sub.add_parser("doctor", help="check adapter readiness")
    p_adapter_doctor.add_argument("agent", choices=["generic-cli", "claude-code", "kimi-code"])
    p_adapter_doctor.add_argument("--sandbox", help="path to SANDBOX_CONTRACT.json")
    p_adapter_doctor.set_defaults(func=cmd_adapter_doctor)
    p_adapter_smoke = adapter_sub.add_parser("smoke", help="run an opt-in real adapter smoke test")
    p_adapter_smoke.add_argument("agent", choices=["claude-code", "kimi-code"])
    p_adapter_smoke.add_argument("--workspace", default=".", help="workspace root")
    p_adapter_smoke.add_argument("--timeout-seconds", type=int, default=120)
    p_adapter_smoke.add_argument("--max-output-bytes", type=int, default=80000)
    p_adapter_smoke.add_argument("--max-budget-usd", type=float, default=0.05)
    p_adapter_smoke.set_defaults(func=cmd_adapter_smoke)
    p_adapter_scaffold = adapter_sub.add_parser("scaffold", help="create disabled adapter onboarding files")
    p_adapter_scaffold.add_argument("agent")
    p_adapter_scaffold.add_argument("--output-dir", default=".", help="directory for generated adapter onboarding files")
    p_adapter_scaffold.add_argument("--force", action="store_true", help="overwrite existing generated files")
    p_adapter_scaffold.set_defaults(func=cmd_adapter_scaffold)
    p_adapter_matrix = adapter_sub.add_parser("matrix", help="show adapter readiness and promotion matrix")
    p_adapter_matrix.add_argument("--doctor", action="store_true", help="probe implemented adapters and include doctor status")
    p_adapter_matrix.add_argument("--output", help="write matrix JSON to this path")
    p_adapter_matrix.add_argument("--html", help="also write a static HTML matrix to this path")
    p_adapter_matrix.set_defaults(func=cmd_adapter_matrix)

    p_dispatch = sub.add_parser("dispatch", help="manage dispatch queue")
    dispatch_sub = p_dispatch.add_subparsers(dest="dispatch_command", required=True)

    p_dispatch_queue = dispatch_sub.add_parser("queue", help="queue a dispatch for an agent")
    p_dispatch_queue.add_argument("task_id")
    p_dispatch_queue.add_argument("--agent", default="generic-cli")
    p_dispatch_queue.add_argument("--title", required=True)
    p_dispatch_queue.add_argument("--instructions", required=True)
    p_dispatch_queue.add_argument("--require-ready", action="store_true", help="block queueing unless adapter matrix readiness is READY_SUPERVISED")
    p_dispatch_queue.add_argument("--sandbox", help="optional sandbox contract reference for gate context")
    p_dispatch_queue.add_argument("--workspace", default=".", help="workspace root")
    p_dispatch_queue.set_defaults(func=cmd_dispatch_queue)

    p_dispatch_list = dispatch_sub.add_parser("list", help="list task dispatches")
    p_dispatch_list.add_argument("task_id")
    p_dispatch_list.add_argument("--workspace", default=".", help="workspace root")
    p_dispatch_list.set_defaults(func=cmd_dispatch_list)

    p_dispatch_claim = dispatch_sub.add_parser("claim", help="claim a queued dispatch")
    p_dispatch_claim.add_argument("task_id")
    p_dispatch_claim.add_argument("dispatch_id")
    p_dispatch_claim.add_argument("--agent", default="generic-cli")
    p_dispatch_claim.add_argument("--workspace", default=".", help="workspace root")
    p_dispatch_claim.set_defaults(func=cmd_dispatch_claim)

    p_dispatch_complete = dispatch_sub.add_parser("complete", help="complete a dispatch")
    p_dispatch_complete.add_argument("task_id")
    p_dispatch_complete.add_argument("dispatch_id")
    p_dispatch_complete.add_argument("--agent", default="generic-cli")
    p_dispatch_complete.add_argument("--summary", required=True)
    p_dispatch_complete.add_argument("--workspace", default=".", help="workspace root")
    p_dispatch_complete.set_defaults(func=cmd_dispatch_complete)

    p_dispatch_execute = dispatch_sub.add_parser("execute", help="execute a dispatch through adapter gates")
    p_dispatch_execute.add_argument("task_id")
    p_dispatch_execute.add_argument("dispatch_id")
    p_dispatch_execute.add_argument("--agent", default="generic-cli")
    p_dispatch_execute.add_argument("--sandbox", help="path to SANDBOX_CONTRACT.json")
    p_dispatch_execute.add_argument("--dry-run", action="store_true", help="validate gates without running an external CLI")
    p_dispatch_execute.add_argument("--command-json", help='safe command as JSON array, e.g. ["echo","hello"]')
    p_dispatch_execute.add_argument("--prompt-file", help="task-local prompt file for first-party supervised adapters")
    p_dispatch_execute.add_argument("--timeout-seconds", type=int, default=10)
    p_dispatch_execute.add_argument("--max-output-bytes", type=int, default=20000)
    p_dispatch_execute.add_argument("--max-budget-usd", type=float, default=0.25)
    p_dispatch_execute.add_argument("--workspace", default=".", help="workspace root")
    p_dispatch_execute.set_defaults(func=cmd_dispatch_execute)

    p_dashboard = sub.add_parser("dashboard", help="render a static dashboard for a task")
    p_dashboard.add_argument("task_id")
    p_dashboard.add_argument("--workspace", default=".", help="workspace root")
    p_dashboard.set_defaults(func=cmd_dashboard)

    p_dashboard_serve = sub.add_parser("serve", help="serve a workspace directory over HTTP")
    p_dashboard_serve.add_argument("--workspace", default=".", help="workspace root")
    p_dashboard_serve.add_argument("--host", default="127.0.0.1")
    p_dashboard_serve.add_argument("--port", type=int, default=8765)
    p_dashboard_serve.set_defaults(func=cmd_dashboard_serve)

    p_orchestrate = sub.add_parser("orchestrate-start", help="create a task and initialize a workflow plan")
    p_orchestrate.add_argument("title")
    p_orchestrate.add_argument("--request")
    p_orchestrate.add_argument("--template", default="hello-multi-cli")
    p_orchestrate.add_argument("--workspace", default=".", help="workspace root")
    p_orchestrate.set_defaults(func=cmd_orchestrate_start)

    p_workflow = sub.add_parser("workflow", help="inspect and advance workflow plans")
    workflow_sub = p_workflow.add_subparsers(dest="workflow_command", required=True)
    p_workflow_status = workflow_sub.add_parser("status", help="show workflow phase state")
    p_workflow_status.add_argument("task_id")
    p_workflow_status.add_argument("--workspace", default=".", help="workspace root")
    p_workflow_status.set_defaults(func=cmd_workflow_status)
    p_workflow_advance = workflow_sub.add_parser("advance", help="advance the current workflow phase")
    p_workflow_advance.add_argument("task_id")
    p_workflow_advance.add_argument("--phase", required=True)
    p_workflow_advance.add_argument("--verdict", required=True, choices=["pass", "fail"])
    p_workflow_advance.add_argument("--summary", required=True)
    p_workflow_advance.add_argument("--auto-dispatch", action="store_true", help="queue the next phase dispatch after a passing phase")
    p_workflow_advance.add_argument("--require-ready", action="store_true", help="apply adapter readiness gate to auto-dispatch")
    p_workflow_advance.add_argument("--workspace", default=".", help="workspace root")
    p_workflow_advance.set_defaults(func=cmd_workflow_advance)

    p_schema = sub.add_parser("schema", help="schema utilities")
    schema_sub = p_schema.add_subparsers(dest="schema_command", required=True)
    p_schema_validate = schema_sub.add_parser("validate", help="validate a schema document")
    p_schema_validate.add_argument("kind", choices=["loop-spec", "adapter-manifest", "sandbox-contract", "run-ledger"])
    p_schema_validate.add_argument("path")
    p_schema_validate.set_defaults(func=cmd_schema_validate)

    p_audit = sub.add_parser("audit", help="run minimal safety audit")
    p_audit.add_argument("path", nargs="?", default=".", help="path to audit")
    p_audit.set_defaults(func=cmd_audit)

    p_demo = sub.add_parser("demo", help="run built-in demos")
    demo_sub = p_demo.add_subparsers(dest="demo_command", required=True)
    p_demo_hello = demo_sub.add_parser("hello-multi-cli", help="run sanitized hello multi-CLI demo")
    p_demo_hello.add_argument("--workspace", default=".mco-demo", help="workspace root")
    p_demo_hello.set_defaults(func=cmd_demo_hello)
    p_demo_walkthrough = demo_sub.add_parser("walkthrough", help="generate a complete public walkthrough bundle")
    p_demo_walkthrough.add_argument("--workspace", default=".mco-walkthrough", help="workspace root")
    p_demo_walkthrough.add_argument("--output-dir", default=".mco-walkthrough-output", help="walkthrough output directory")
    p_demo_walkthrough.set_defaults(func=cmd_demo_walkthrough)

    p_run = sub.add_parser("run", help="run read-only replay utilities")
    run_sub = p_run.add_subparsers(dest="run_command", required=True)
    p_run_replay = run_sub.add_parser("replay", help="read RUN_LEDGER.json and print a replay timeline")
    p_run_replay.add_argument("ledger", help="path to RUN_LEDGER.json")
    p_run_replay.add_argument("--json", action="store_true", help="print structured JSON")
    p_run_replay.set_defaults(func=cmd_run_replay)

    p_usage = sub.add_parser("usage", help="usage and quota evidence utilities")
    usage_sub = p_usage.add_subparsers(dest="usage_command", required=True)
    p_usage_snapshot = usage_sub.add_parser("snapshot", help="write a task-local usage evidence snapshot")
    p_usage_snapshot.add_argument("task_id")
    p_usage_snapshot.add_argument("--workspace", default=".", help="workspace root")
    p_usage_snapshot.set_defaults(func=cmd_usage_snapshot)

    p_release = sub.add_parser("release", help="release readiness utilities")
    release_sub = p_release.add_subparsers(dest="release_command", required=True)
    p_release_check = release_sub.add_parser("check", help="run release readiness checks")
    p_release_check.add_argument("path", nargs="?", default=".", help="repository path")
    p_release_check.add_argument("--json", action="store_true", help="print structured JSON")
    p_release_check.set_defaults(func=cmd_release_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
