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


def run_mco(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "mco.cli", *args],
        cwd=cwd or ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


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
            self.assertIn("Boss Dashboard Seed", dashboard_path.read_text(encoding="utf-8"))

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
            ("dispatch", "--help"),
            ("schema", "--help"),
            ("orchestrate-start", "--help"),
            ("demo", "--help"),
            ("run", "--help"),
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
