from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_mco(*args: str, cwd: Path | None = None, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "mco.cli", *args],
        cwd=cwd or ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def write_fake_claude(path: Path, fail_budget: bool = False) -> None:
    script = f"""#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("2.1.140 (Claude Code)")
    raise SystemExit(0)
if args == ["--help"]:
    print("--print --output-format --max-budget-usd --no-session-persistence --permission-mode --tools")
    raise SystemExit(0)
if args == ["auth", "status"]:
    print(json.dumps({{"loggedIn": True, "authMethod": "oauth_token", "apiProvider": "firstParty"}}))
    raise SystemExit(0)
if "--print" in args:
    if {str(fail_budget)}:
        print(json.dumps({{"type": "result", "subtype": "error_max_budget_usd", "is_error": True}}))
        raise SystemExit(1)
    print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "result": "MCO_ADAPTER_SMOKE_OK", "total_cost_usd": 0.0123}}))
    raise SystemExit(0)
print("unexpected args", args)
raise SystemExit(2)
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_fake_kimi(path: Path, fail_prompt: bool = False) -> None:
    script = f"""#!/usr/bin/env python3
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("0.20.3")
    raise SystemExit(0)
if args == ["--help"]:
    print("-p, --prompt <prompt>")
    print("--output-format <format>")
    raise SystemExit(0)
if args == ["doctor"]:
    print("Kimi Code configuration OK")
    raise SystemExit(0)
if "--prompt" in args:
    if {str(fail_prompt)}:
        print("simulated kimi failure")
        raise SystemExit(1)
    print("MCO_ADAPTER_SMOKE_OK")
    raise SystemExit(0)
print("unexpected args", args)
raise SystemExit(2)
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


class WorkspaceTests(unittest.TestCase):
    def test_init_and_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            init = run_mco("init", "--workspace", str(workspace))
            self.assertEqual(init.returncode, 0, init.stderr)

            doctor = run_mco("doctor", "--workspace", str(workspace))
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("PASS config", doctor.stdout)
            self.assertIn("PASS loop_spec_template", doctor.stdout)

            config = json.loads((workspace / ".mco" / "config.json").read_text())
            self.assertEqual(config["schema"], "mco.workspace.v0.2")

    def test_task_create_list_and_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)

            created = run_mco("task", "create", "Hello Multi CLI", "--workspace", str(workspace))
            self.assertEqual(created.returncode, 0, created.stderr)
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))

            listed = run_mco("task", "list", "--workspace", str(workspace))
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn(task_id, listed.stdout)

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            dashboard_path = workspace / "tasks" / task_id / "dashboard.html"
            self.assertTrue(dashboard_path.exists())
            self.assertIn("Boss Dashboard Control Room", dashboard_path.read_text(encoding="utf-8"))

    def test_task_create_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)

            created = run_mco("task", "create", "JSON Task", "--json", "--workspace", str(workspace))
            self.assertEqual(created.returncode, 0, created.stderr)
            payload = json.loads(created.stdout)
            self.assertTrue(payload["task_id"].endswith("json-task"))
            self.assertTrue(Path(payload["task_dir"]).exists())
            self.assertTrue(Path(payload["loop_spec"]).exists())
            self.assertTrue(Path(payload["run_ledger"]).exists())

    def test_status_defaults_to_latest_task_and_summarizes_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            first = run_mco("task", "create", "First Task", "--workspace", str(workspace))
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_mco("task", "create", "Second Task", "--workspace", str(workspace))
            self.assertEqual(second.returncode, 0, second.stderr)
            task_id = next(line.split(": ", 1)[1] for line in second.stdout.splitlines() if line.startswith("created task:"))

            blocked = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "mimo-code",
                "--title",
                "Blocked worker",
                "--instructions",
                "Should not reach inbox.",
                "--require-ready",
                "--workspace",
                str(workspace),
            )
            self.assertNotEqual(blocked.returncode, 0)

            status = run_mco("status", "--workspace", str(workspace))
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertIn("Second Task", status.stdout)
            self.assertIn("blocked=1", status.stdout)
            self.assertIn("mimo-code: DISABLED", status.stdout)
            self.assertIn("gate=requires-review", status.stdout)

            status_json = run_mco("status", "--json", "--workspace", str(workspace))
            self.assertEqual(status_json.returncode, 0, status_json.stdout + status_json.stderr)
            payload = json.loads(status_json.stdout)
            self.assertEqual(payload["schema"], "mco.status.v1.0")
            self.assertEqual(payload["task"]["task_id"], task_id)
            self.assertEqual(payload["dispatch"]["counts"]["blocked"], 1)

    def test_event_artifact_status_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Evidence Task", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))

            event = run_mco(
                "task",
                "event",
                task_id,
                "--type",
                "verification",
                "--message",
                "Unit test evidence event.",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(event.returncode, 0, event.stderr)
            self.assertIn("verification", event.stdout)

            artifact_path = workspace / "sample-artifact.md"
            artifact_path.write_text("# Sample\n", encoding="utf-8")
            registered = run_mco(
                "artifact",
                "register",
                task_id,
                str(artifact_path),
                "--label",
                "sample",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(registered.returncode, 0, registered.stderr)
            self.assertIn("sample", registered.stdout)

            status = run_mco("task", "status", task_id, "--workspace", str(workspace))
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("Evidence Task", status.stdout)

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            dashboard_html = (workspace / "tasks" / task_id / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Artifacts", dashboard_html)
            self.assertIn("sample", dashboard_html)

            audit = run_mco("audit", str(ROOT))
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            self.assertIn("FAIL=0", audit.stdout)

    def test_orchestrate_start_and_schema_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)

            started = run_mco(
                "orchestrate-start",
                "Hello Orchestrated Task",
                "--template",
                "hello-multi-cli",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            task_id = next(line.split(": ", 1)[1] for line in started.stdout.splitlines() if line.startswith("created task:"))
            task_dir = workspace / "tasks" / task_id
            self.assertTrue((task_dir / "plan.json").exists())
            self.assertTrue((task_dir / "dashboard.html").exists())

            loop_check = run_mco("schema", "validate", "loop-spec", str(task_dir / "LOOP_SPEC.json"))
            self.assertEqual(loop_check.returncode, 0, loop_check.stdout + loop_check.stderr)
            ledger_check = run_mco("schema", "validate", "run-ledger", str(task_dir / "RUN_LEDGER.json"))
            self.assertEqual(ledger_check.returncode, 0, ledger_check.stdout + ledger_check.stderr)

    def test_disabled_adapter_templates_validate_and_do_not_execute(self) -> None:
        for path in sorted((ROOT / "templates" / "adapters").glob("*.json")):
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(payload["can_run_shell"])
                self.assertEqual(payload["quota_status"], "unknown")
                check = run_mco("schema", "validate", "adapter-manifest", str(path))
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_adapter_scaffold_writes_disabled_onboarding_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "adapter-kit"
            scaffold = run_mco("adapter", "scaffold", "new-cli", "--output-dir", str(out_dir))
            self.assertEqual(scaffold.returncode, 0, scaffold.stdout + scaffold.stderr)
            payload = json.loads(scaffold.stdout)
            self.assertEqual(payload["schema"], "mco.adapter_scaffold.v1.0")
            self.assertEqual(payload["agent"], "new-cli")
            manifest = out_dir / "new-cli.adapter.json"
            sandbox = out_dir / "new-cli.sandbox.json"
            checklist = out_dir / "new-cli-smoke-checklist.md"
            self.assertTrue(manifest.exists())
            self.assertTrue(sandbox.exists())
            self.assertTrue(checklist.exists())

            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertFalse(manifest_payload["supervised"])
            self.assertFalse(manifest_payload["can_run_shell"])
            manifest_check = run_mco("schema", "validate", "adapter-manifest", str(manifest))
            self.assertEqual(manifest_check.returncode, 0, manifest_check.stdout + manifest_check.stderr)
            sandbox_check = run_mco("schema", "validate", "sandbox-contract", str(sandbox))
            self.assertEqual(sandbox_check.returncode, 0, sandbox_check.stdout + sandbox_check.stderr)

            blocked = run_mco("adapter", "scaffold", "new-cli", "--output-dir", str(out_dir))
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("refusing to overwrite", blocked.stderr)

    def test_claude_code_adapter_doctor_and_supervised_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_claude = tmp_path / "claude"
            write_fake_claude(fake_claude)
            env = {"CLAUDE_CODE_BIN": str(fake_claude)}

            capabilities = run_mco("adapter", "capabilities", "claude-code", env_extra=env)
            self.assertEqual(capabilities.returncode, 0, capabilities.stdout + capabilities.stderr)
            manifest = json.loads(capabilities.stdout)
            self.assertTrue(manifest["supervised"])
            self.assertFalse(manifest["can_run_shell"])

            sandbox = tmp_path / "claude-sandbox.json"
            sandbox.write_text((ROOT / "templates" / "sandbox-contracts" / "claude-code-supervised.json").read_text(encoding="utf-8"), encoding="utf-8")
            doctor = run_mco("adapter", "doctor", "claude-code", "--sandbox", str(sandbox), env_extra=env)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            doctor_payload = json.loads(doctor.stdout)
            self.assertEqual(doctor_payload["status"], "READY_SUPERVISED")

            workspace = tmp_path / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Claude Adapter Task", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "claude-code",
                "--title",
                "Smoke prompt",
                "--instructions",
                "Return a fixed smoke string.",
                "--workspace",
                str(workspace),
            )
            dispatch_id = json.loads(queued.stdout)["dispatch_id"]
            task_dir = workspace / "tasks" / task_id
            prompt = task_dir / "prompt.md"
            prompt.write_text("Return exactly: MCO_ADAPTER_SMOKE_OK\n", encoding="utf-8")

            executed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "claude-code",
                "--sandbox",
                str(sandbox),
                "--prompt-file",
                str(prompt),
                "--timeout-seconds",
                "30",
                "--max-output-bytes",
                "20000",
                "--max-budget-usd",
                "0.25",
                "--workspace",
                str(workspace),
                env_extra=env,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            dispatch = json.loads(executed.stdout)
            self.assertEqual(dispatch["status"], "completed")
            report_path = task_dir / "artifacts" / f"{dispatch_id}-claude-execution-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["success"])
            self.assertIn("MCO_ADAPTER_SMOKE_OK", report["stdout"])

            usage = run_mco("usage", "snapshot", task_id, "--workspace", str(workspace))
            self.assertEqual(usage.returncode, 0, usage.stdout + usage.stderr)
            usage_payload = json.loads((task_dir / "USAGE_SNAPSHOT.json").read_text(encoding="utf-8"))
            self.assertEqual(usage_payload["schema"], "mco.usage_snapshot.v1.0")
            self.assertEqual(usage_payload["agents"][0]["agent"], "claude-code")
            self.assertEqual(usage_payload["agents"][0]["quota_status"], "budget_limited")
            self.assertAlmostEqual(usage_payload["agents"][0]["observed_cost_usd_total"], 0.0123)

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            dashboard_html = (task_dir / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Control Room", dashboard_html)
            self.assertIn("Adapter Readiness", dashboard_html)
            self.assertIn("Usage Snapshot", dashboard_html)
            self.assertIn("claude-code", dashboard_html)
            self.assertIn("$0.0123 / $0.2500", dashboard_html)
            self.assertIn("No owner action required", dashboard_html)

    def test_claude_code_adapter_smoke_creates_evidence_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_claude = tmp_path / "claude"
            write_fake_claude(fake_claude)
            env = {"CLAUDE_CODE_BIN": str(fake_claude)}
            workspace = tmp_path / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)

            smoke = run_mco(
                "adapter",
                "smoke",
                "claude-code",
                "--workspace",
                str(workspace),
                "--timeout-seconds",
                "30",
                "--max-budget-usd",
                "0.05",
                env_extra=env,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            payload = json.loads(smoke.stdout)
            self.assertEqual(payload["schema"], "mco.adapter_smoke.v1.0")
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["agent"], "claude-code")
            self.assertTrue(Path(payload["execution_report"]).exists())
            self.assertTrue(Path(payload["usage_snapshot"]).exists())
            self.assertTrue(Path(payload["dashboard"]).exists())
            self.assertIn("MCO_ADAPTER_SMOKE_OK", Path(payload["execution_report"]).read_text(encoding="utf-8"))

    def test_kimi_code_adapter_doctor_execution_and_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_kimi = tmp_path / "kimi"
            write_fake_kimi(fake_kimi)
            env = {"KIMI_CODE_BIN": str(fake_kimi)}

            capabilities = run_mco("adapter", "capabilities", "kimi-code", env_extra=env)
            self.assertEqual(capabilities.returncode, 0, capabilities.stdout + capabilities.stderr)
            manifest = json.loads(capabilities.stdout)
            self.assertTrue(manifest["supervised"])
            self.assertEqual(manifest["quota_status"], "unknown")
            self.assertFalse(manifest["can_run_shell"])

            sandbox = tmp_path / "kimi-sandbox.json"
            sandbox.write_text((ROOT / "templates" / "sandbox-contracts" / "kimi-code-supervised.json").read_text(encoding="utf-8"), encoding="utf-8")
            doctor = run_mco("adapter", "doctor", "kimi-code", "--sandbox", str(sandbox), env_extra=env)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            doctor_payload = json.loads(doctor.stdout)
            self.assertEqual(doctor_payload["status"], "READY_SUPERVISED")

            workspace = tmp_path / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Kimi Adapter Task", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "kimi-code",
                "--title",
                "Smoke prompt",
                "--instructions",
                "Return a fixed smoke string.",
                "--workspace",
                str(workspace),
            )
            dispatch_id = json.loads(queued.stdout)["dispatch_id"]
            task_dir = workspace / "tasks" / task_id
            prompt = task_dir / "prompt.md"
            prompt.write_text("Return exactly: MCO_ADAPTER_SMOKE_OK\n", encoding="utf-8")

            executed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "kimi-code",
                "--sandbox",
                str(sandbox),
                "--prompt-file",
                str(prompt),
                "--timeout-seconds",
                "30",
                "--workspace",
                str(workspace),
                env_extra=env,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            report_path = task_dir / "artifacts" / f"{dispatch_id}-kimi-execution-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["success"])
            self.assertEqual(report["quota_status"], "unknown")
            self.assertIn("MCO_ADAPTER_SMOKE_OK", report["stdout"])

            usage = run_mco("usage", "snapshot", task_id, "--workspace", str(workspace))
            self.assertEqual(usage.returncode, 0, usage.stdout + usage.stderr)
            usage_payload = json.loads((task_dir / "USAGE_SNAPSHOT.json").read_text(encoding="utf-8"))
            self.assertEqual(usage_payload["agents"][0]["agent"], "kimi-code")
            self.assertEqual(usage_payload["agents"][0]["quota_status"], "unknown")

            smoke = run_mco(
                "adapter",
                "smoke",
                "kimi-code",
                "--workspace",
                str(workspace),
                "--timeout-seconds",
                "30",
                env_extra=env,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            smoke_payload = json.loads(smoke.stdout)
            self.assertEqual(smoke_payload["status"], "PASS")
            self.assertEqual(smoke_payload["agent"], "kimi-code")
            self.assertTrue(Path(smoke_payload["execution_report"]).exists())

    def test_adapter_matrix_reports_supported_and_disabled_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_claude = tmp_path / "claude"
            fake_kimi = tmp_path / "kimi"
            write_fake_claude(fake_claude)
            write_fake_kimi(fake_kimi)
            env = {"CLAUDE_CODE_BIN": str(fake_claude), "KIMI_CODE_BIN": str(fake_kimi)}

            matrix = run_mco("adapter", "matrix", env_extra=env)
            self.assertEqual(matrix.returncode, 0, matrix.stdout + matrix.stderr)
            payload = json.loads(matrix.stdout)
            self.assertEqual(payload["schema"], "mco.adapter_matrix.v1.0")
            agents = {item["agent"]: item for item in payload["agents"]}
            self.assertTrue(agents["claude-code"]["implemented"])
            self.assertTrue(agents["kimi-code"]["implemented"])
            self.assertFalse(agents["mimo-code"]["implemented"])
            self.assertEqual(agents["mimo-code"]["readiness"], "DISABLED")
            self.assertEqual(agents["kimi-code"]["quota_status"], "unknown")
            self.assertTrue(agents["claude-code"]["per_run_budget_cap"])
            self.assertFalse(agents["kimi-code"]["per_run_budget_cap"])

            out_json = tmp_path / "matrix.json"
            out_html = tmp_path / "matrix.html"
            written = run_mco(
                "adapter",
                "matrix",
                "--doctor",
                "--output",
                str(out_json),
                "--html",
                str(out_html),
                env_extra=env,
            )
            self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
            written_payload = json.loads(written.stdout)
            self.assertEqual(written_payload["json"], str(out_json.resolve()))
            self.assertEqual(written_payload["html"], str(out_html.resolve()))
            matrix_payload = json.loads(out_json.read_text(encoding="utf-8"))
            doctor_agents = {item["agent"]: item for item in matrix_payload["agents"]}
            self.assertEqual(doctor_agents["claude-code"]["doctor_status"], "READY_SUPERVISED")
            self.assertEqual(doctor_agents["kimi-code"]["doctor_status"], "READY_SUPERVISED")
            self.assertIn("Adapter Matrix", out_html.read_text(encoding="utf-8"))

    def test_dispatch_require_ready_blocks_disabled_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Gated Dispatch", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            task_dir = workspace / "tasks" / task_id

            blocked = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "mimo-code",
                "--title",
                "Disabled work",
                "--instructions",
                "Should not enter inbox.",
                "--require-ready",
                "--workspace",
                str(workspace),
            )
            self.assertNotEqual(blocked.returncode, 0)
            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["gate"]["readiness"], "DISABLED")
            self.assertFalse((task_dir / "dispatch" / "agent-inbox" / "mimo-code" / f"{payload['dispatch_id']}.md").exists())
            ledger = json.loads((task_dir / "RUN_LEDGER.json").read_text(encoding="utf-8"))
            self.assertIn("dispatch_gate_blocked", [event["type"] for event in ledger["events"]])

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stdout + dashboard.stderr)
            dashboard_html = (task_dir / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Adapter Matrix", dashboard_html)
            self.assertIn("Dispatch Gate Status", dashboard_html)
            self.assertIn("mimo-code", dashboard_html)
            self.assertIn("adapter readiness is DISABLED", dashboard_html)

    def test_dispatch_require_ready_allows_ready_supervised_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_claude = tmp_path / "claude"
            fake_kimi = tmp_path / "kimi"
            write_fake_claude(fake_claude)
            write_fake_kimi(fake_kimi)
            env = {"CLAUDE_CODE_BIN": str(fake_claude), "KIMI_CODE_BIN": str(fake_kimi)}
            workspace = tmp_path / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Ready Dispatch", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            task_dir = workspace / "tasks" / task_id

            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "kimi-code",
                "--title",
                "Ready work",
                "--instructions",
                "May enter inbox.",
                "--require-ready",
                "--workspace",
                str(workspace),
                env_extra=env,
            )
            self.assertEqual(queued.returncode, 0, queued.stdout + queued.stderr)
            payload = json.loads(queued.stdout)
            self.assertEqual(payload["status"], "queued")
            self.assertEqual(payload["gate"]["readiness"], "READY_SUPERVISED")
            self.assertTrue((task_dir / "dispatch" / "agent-inbox" / "kimi-code" / f"{payload['dispatch_id']}.md").exists())

    def test_claude_code_adapter_records_budget_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_claude = tmp_path / "claude"
            write_fake_claude(fake_claude, fail_budget=True)
            env = {"CLAUDE_CODE_BIN": str(fake_claude)}
            workspace = tmp_path / "workspace"
            sandbox = tmp_path / "claude-sandbox.json"
            sandbox.write_text((ROOT / "templates" / "sandbox-contracts" / "claude-code-supervised.json").read_text(encoding="utf-8"), encoding="utf-8")

            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Claude Budget Task", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "claude-code",
                "--title",
                "Budget prompt",
                "--instructions",
                "Trigger budget error.",
                "--workspace",
                str(workspace),
            )
            dispatch_id = json.loads(queued.stdout)["dispatch_id"]
            task_dir = workspace / "tasks" / task_id
            prompt = task_dir / "prompt.md"
            prompt.write_text("Return exactly: MCO_ADAPTER_SMOKE_OK\n", encoding="utf-8")

            executed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "claude-code",
                "--sandbox",
                str(sandbox),
                "--prompt-file",
                str(prompt),
                "--timeout-seconds",
                "30",
                "--workspace",
                str(workspace),
                env_extra=env,
            )
            self.assertNotEqual(executed.returncode, 0)
            report_path = task_dir / "artifacts" / f"{dispatch_id}-claude-execution-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["success"])
            self.assertIn("error_max_budget_usd", report["summary"])

            usage = run_mco("usage", "snapshot", task_id, "--workspace", str(workspace))
            self.assertEqual(usage.returncode, 0, usage.stdout + usage.stderr)
            usage_payload = json.loads((task_dir / "USAGE_SNAPSHOT.json").read_text(encoding="utf-8"))
            self.assertEqual(usage_payload["agents"][0]["quota_status"], "needs_attention")
            self.assertIn("error_max_budget_usd", usage_payload["agents"][0]["last_error"])

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            dashboard_html = (task_dir / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Owner Escalations", dashboard_html)
            self.assertIn("error_max_budget_usd", dashboard_html)
            self.assertIn("NEEDS_ATTENTION", dashboard_html)

    def test_release_check_passes_without_git_failure(self) -> None:
        for path in ROOT.rglob("__pycache__"):
            shutil.rmtree(path)
        result = run_mco("release", "check", str(ROOT), "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["fail_count"], 0)

    def test_release_and_audit_ignore_local_install_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            shutil.copytree(
                ROOT,
                fixture,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.egg-info"),
            )
            vendored = fixture / ".venv" / "lib" / "python3.14" / "site-packages" / "pip" / "_internal" / "commands"
            vendored.mkdir(parents=True)
            (vendored / "configuration.py").write_text("subprocess.run(cmd, " + "shell" + "=True)\n", encoding="utf-8")
            (vendored / "private.md").write_text(
                "private path: " + "/" + "Users" + "/" + "liuyang" + "\n",
                encoding="utf-8",
            )

            release = run_mco("release", "check", str(fixture), "--json")
            self.assertEqual(release.returncode, 0, release.stdout + release.stderr)
            release_payload = json.loads(release.stdout)
            self.assertEqual(release_payload["fail_count"], 0)

            audit = run_mco("audit", str(fixture))
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)

    def test_command_help_smoke(self) -> None:
        commands = [
            ("--help",),
            ("task", "--help"),
            ("artifact", "--help"),
            ("adapter", "--help"),
            ("adapter", "matrix", "--help"),
            ("adapter", "scaffold", "--help"),
            ("adapter", "smoke", "--help"),
            ("dispatch", "--help"),
            ("dispatch", "queue", "--help"),
            ("schema", "--help"),
            ("orchestrate-start", "--help"),
            ("demo", "--help"),
            ("run", "--help"),
            ("usage", "--help"),
            ("audit", "--help"),
            ("release", "--help"),
        ]
        for command in commands:
            with self.subTest(command=command):
                result = run_mco(*command)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_audit_fails_on_bad_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "bad.md"
            fixture.write_text("private path: " + "/" + "Users" + "/" + "liuyang" + "\n", encoding="utf-8")
            audit = run_mco("audit", tmp)
            self.assertNotEqual(audit.returncode, 0)
            self.assertIn("FAIL=1", audit.stdout)

    def test_generic_dispatch_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Dispatch Task", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))

            capabilities = run_mco("adapter", "capabilities", "generic-cli")
            self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
            self.assertIn("generic-cli", capabilities.stdout)

            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "generic-cli",
                "--title",
                "Generic Work",
                "--instructions",
                "Write evidence only.",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(queued.returncode, 0, queued.stderr)
            payload = json.loads(queued.stdout)
            dispatch_id = payload["dispatch_id"]

            listed = run_mco("dispatch", "list", task_id, "--workspace", str(workspace))
            self.assertIn(dispatch_id, listed.stdout)
            self.assertIn("queued", listed.stdout)

            claimed = run_mco("dispatch", "claim", task_id, dispatch_id, "--agent", "generic-cli", "--workspace", str(workspace))
            self.assertEqual(claimed.returncode, 0, claimed.stderr)
            self.assertIn("claimed", claimed.stdout)

            completed = run_mco(
                "dispatch",
                "complete",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--summary",
                "Done.",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("completed", completed.stdout)

            dashboard = run_mco("dashboard", task_id, "--workspace", str(workspace))
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr)
            dashboard_html = (workspace / "tasks" / task_id / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Dispatches", dashboard_html)
            self.assertIn(dispatch_id, dashboard_html)

    def test_adapter_doctor_and_dispatch_execute_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Sandboxed Dispatch", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            task_dir = workspace / "tasks" / task_id

            sandbox = task_dir / "SANDBOX_CONTRACT.json"
            sandbox.write_text(
                json.dumps(
                    {
                        "schema": "mco.sandbox_contract.v0.2",
                        "worker_id": "generic-single-worker",
                        "agent": "generic-cli",
                        "write_scope": ["task workspace only"],
                        "read_scope": ["task workspace only"],
                        "ports": [],
                        "data_boundary": "no external data",
                        "credential_policy": "no credentials",
                        "merge_owner": "local user",
                        "verification_artifacts": ["RUN_LEDGER.json", "dashboard.html"],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            doctor = run_mco("adapter", "doctor", "generic-cli", "--sandbox", str(sandbox))
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("READY_SUPERVISED", doctor.stdout)

            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "generic-cli",
                "--title",
                "Dry Run Work",
                "--instructions",
                "Validate only.",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(queued.returncode, 0, queued.stderr)
            dispatch_id = json.loads(queued.stdout)["dispatch_id"]

            executed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--sandbox",
                str(sandbox),
                "--dry-run",
                "--workspace",
                str(workspace),
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertIn("completed", executed.stdout)

            ledger = json.loads((task_dir / "RUN_LEDGER.json").read_text(encoding="utf-8"))
            event_types = [event["type"] for event in ledger["events"]]
            self.assertIn("adapter_execution_dry_run", event_types)
            self.assertIn(str(sandbox.resolve()), ledger["sandbox_contract_refs"])
            artifact_labels = [item["label"] for item in ledger["artifacts"] if isinstance(item, dict)]
            self.assertTrue(any(label.endswith("-dry-run") for label in artifact_labels))

            replay = run_mco("run", "replay", str(task_dir / "RUN_LEDGER.json"))
            self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
            self.assertIn("Sandbox contracts:", replay.stdout)
            self.assertIn(str(sandbox.resolve()), replay.stdout)

    def test_dispatch_execute_blocks_without_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
            created = run_mco("task", "create", "Blocked Dispatch", "--workspace", str(workspace))
            task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
            task_dir = workspace / "tasks" / task_id
            queued = run_mco(
                "dispatch",
                "queue",
                task_id,
                "--agent",
                "generic-cli",
                "--title",
                "Unsafe Work",
                "--instructions",
                "Try without sandbox.",
                "--workspace",
                str(workspace),
            )
            dispatch_id = json.loads(queued.stdout)["dispatch_id"]

            blocked = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--dry-run",
                "--workspace",
                str(workspace),
            )
            self.assertNotEqual(blocked.returncode, 0)
            dispatch = json.loads((task_dir / "dispatch" / "dispatches" / f"{dispatch_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(dispatch["status"], "blocked")
            ledger = json.loads((task_dir / "RUN_LEDGER.json").read_text(encoding="utf-8"))
            self.assertIn("dispatch_blocked", [event["type"] for event in ledger["events"]])

    def _create_sandboxed_dispatch(self, workspace: Path, title: str = "Command Work") -> tuple[str, str, Path, Path]:
        self.assertEqual(run_mco("init", "--workspace", str(workspace)).returncode, 0)
        created = run_mco("task", "create", title, "--workspace", str(workspace))
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        task_id = next(line.split(": ", 1)[1] for line in created.stdout.splitlines() if line.startswith("created task:"))
        task_dir = workspace / "tasks" / task_id
        sandbox = task_dir / "SANDBOX_CONTRACT.json"
        sandbox.write_text(
            json.dumps(
                {
                    "schema": "mco.sandbox_contract.v0.2",
                    "worker_id": "generic-single-worker",
                    "agent": "generic-cli",
                    "write_scope": ["task workspace only"],
                    "read_scope": ["task workspace only"],
                    "ports": [],
                    "data_boundary": "no external data",
                    "credential_policy": "no credentials",
                    "merge_owner": "local user",
                    "verification_artifacts": ["RUN_LEDGER.json", "dashboard.html"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        queued = run_mco(
            "dispatch",
            "queue",
            task_id,
            "--agent",
            "generic-cli",
            "--title",
            "Safe Command",
            "--instructions",
            "Execute a safe allowlisted command.",
            "--workspace",
            str(workspace),
        )
        self.assertEqual(queued.returncode, 0, queued.stdout + queued.stderr)
        dispatch_id = json.loads(queued.stdout)["dispatch_id"]
        return task_id, dispatch_id, task_dir, sandbox

    def test_dispatch_execute_safe_echo_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            task_id, dispatch_id, task_dir, sandbox = self._create_sandboxed_dispatch(workspace)

            executed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--sandbox",
                str(sandbox),
                "--command-json",
                json.dumps(["echo", "hello-v1"]),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertIn("completed", executed.stdout)

            report = json.loads((task_dir / "artifacts" / f"{dispatch_id}-execution-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["schema"], "mco.execution_report.v1.0")
            self.assertEqual(report["exit_code"], 0)
            self.assertIn("hello-v1", report["stdout"])
            self.assertEqual(report["cwd"], str(task_dir.resolve()))

            ledger = json.loads((task_dir / "RUN_LEDGER.json").read_text(encoding="utf-8"))
            event_types = [event["type"] for event in ledger["events"]]
            self.assertIn("adapter_execution", event_types)
            self.assertIn("dispatch_completed", event_types)

    def test_dispatch_execute_safe_command_failure_records_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            task_id, dispatch_id, task_dir, sandbox = self._create_sandboxed_dispatch(workspace, "Failing Command")

            failed = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--sandbox",
                str(sandbox),
                "--command-json",
                json.dumps(["python", "-c", "print(1/0)"]),
                "--workspace",
                str(workspace),
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("ERROR: safe command failed", failed.stderr)

            dispatch = json.loads((task_dir / "dispatch" / "dispatches" / f"{dispatch_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(dispatch["status"], "failed")
            report = json.loads((task_dir / "artifacts" / f"{dispatch_id}-execution-report.json").read_text(encoding="utf-8"))
            self.assertNotEqual(report["exit_code"], 0)
            self.assertIn("ZeroDivisionError", report["stderr"])

    def test_dispatch_execute_blocks_unsafe_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            task_id, dispatch_id, task_dir, sandbox = self._create_sandboxed_dispatch(workspace, "Unsafe Command")

            unsafe = run_mco(
                "dispatch",
                "execute",
                task_id,
                dispatch_id,
                "--agent",
                "generic-cli",
                "--sandbox",
                str(sandbox),
                "--command-json",
                json.dumps(["python", "-c", "print(__import__('os').getcwd())"]),
                "--workspace",
                str(workspace),
            )
            self.assertNotEqual(unsafe.returncode, 0)
            self.assertIn("disallowed token", unsafe.stderr)
            dispatch = json.loads((task_dir / "dispatch" / "dispatches" / f"{dispatch_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(dispatch["status"], "queued")

    def test_hello_demo_generates_evidence_dashboard_and_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "demo-workspace"
            demo = run_mco("demo", "hello-multi-cli", "--workspace", str(workspace))
            self.assertEqual(demo.returncode, 0, demo.stdout + demo.stderr)
            payload = json.loads(demo.stdout)
            task_dir = Path(payload["task_dir"])

            self.assertTrue((task_dir / "plan.json").exists())
            self.assertTrue((task_dir / "artifacts" / "demo-evidence.md").exists())
            self.assertTrue((task_dir / "dashboard.html").exists())

            ledger = json.loads((task_dir / "RUN_LEDGER.json").read_text(encoding="utf-8"))
            event_types = [event["type"] for event in ledger["events"]]
            self.assertIn("dispatch_queued", event_types)
            self.assertIn("dispatch_claimed", event_types)
            self.assertIn("dispatch_completed", event_types)

            dashboard_html = (task_dir / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Demo Evidence", (task_dir / "artifacts" / "demo-evidence.md").read_text(encoding="utf-8"))
            self.assertIn("Dispatches", dashboard_html)
            self.assertIn("completed", dashboard_html)

            replay = run_mco("run", "replay", str(task_dir / "RUN_LEDGER.json"))
            self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
            self.assertIn("Run replay:", replay.stdout)
            self.assertIn("Workflow: hello-multi-cli", replay.stdout)
            self.assertIn("dispatch_completed", replay.stdout)

            replay_json = run_mco("run", "replay", str(task_dir / "RUN_LEDGER.json"), "--json")
            self.assertEqual(replay_json.returncode, 0, replay_json.stdout + replay_json.stderr)
            parsed = json.loads(replay_json.stdout)
            self.assertEqual(parsed["schema"], "mco.replay.v0.5")
            self.assertEqual(parsed["workflow"], "hello-multi-cli")
            self.assertGreaterEqual(parsed["event_count"], 5)

    def test_repository_has_no_private_user_paths(self) -> None:
        forbidden = [
            "/" + "Users" + "/" + "liuyang",
            "AI" + "-Agent" + "-Vault" + "/.agent-state/tasks/" + "20260623" + "-142151-demo",
        ]
        checked_suffixes = {".py", ".md", ".json", ".toml", ".yml", ".yaml"}
        offenders = []
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or path.is_dir() or path.suffix not in checked_suffixes:
                continue
            text = path.read_text(encoding="utf-8")
            for needle in forbidden:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)} contains {needle}")
        self.assertFalse(offenders, "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
