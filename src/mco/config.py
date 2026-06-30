from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


CONFIG_DIR = ".mco"
CONFIG_FILE = "config.json"


@dataclass(frozen=True)
class WorkspaceConfig:
    workspace_root: Path

    @property
    def config_dir(self) -> Path:
        return self.workspace_root / CONFIG_DIR

    @property
    def tasks_dir(self) -> Path:
        return self.workspace_root / "tasks"

    @property
    def runs_dir(self) -> Path:
        return self.workspace_root / "runs"

    @property
    def artifacts_dir(self) -> Path:
        return self.workspace_root / "artifacts"

    @property
    def config_path(self) -> Path:
        return self.config_dir / CONFIG_FILE


def resolve_workspace(path: str | None) -> WorkspaceConfig:
    root = Path(path or ".").expanduser().resolve()
    return WorkspaceConfig(workspace_root=root)


def init_workspace(config: WorkspaceConfig) -> None:
    for directory in [
        config.workspace_root,
        config.config_dir,
        config.tasks_dir,
        config.runs_dir,
        config.artifacts_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema": "mco.workspace.v0.2",
        "workspace_root": str(config.workspace_root),
        "policies": {
            "native_cli_memory_write": "forbidden_by_default",
            "stable_kb_write": "forbidden_by_default",
            "destructive_actions": "explicit_gate_required",
        },
    }
    config.config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_workspace_config(config: WorkspaceConfig) -> dict:
    if not config.config_path.exists():
        raise FileNotFoundError(f"workspace is not initialized: {config.config_path}")
    return json.loads(config.config_path.read_text(encoding="utf-8"))

