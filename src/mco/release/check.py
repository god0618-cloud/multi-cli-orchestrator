from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from mco.audit.safety import audit_tree
from mco.schemas import validate_adapter_manifest


REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "ROADMAP.md",
    ".github/workflows/ci.yml",
    "docs/release-checklist.md",
    "docs/why-multi-cli.md",
    "docs/diagrams.md",
    "docs/adapter-templates.md",
]

GENERATED_PATTERNS = ["__pycache__", ".egg-info", ".pyc"]
IGNORED_TREE_PARTS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "site-packages",
}


@dataclass(frozen=True)
class ReleaseCheckResult:
    pass_count: int
    warn_count: int
    fail_count: int
    findings: list[dict]

    @property
    def ok(self) -> bool:
        return self.fail_count == 0

    def to_dict(self) -> dict:
        return {
            "schema": "mco.release_check.v1.0",
            "pass_count": self.pass_count,
            "warn_count": self.warn_count,
            "fail_count": self.fail_count,
            "findings": self.findings,
        }


def _version_from_init(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError("__version__ not found")
    return match.group(1)


def _version_from_pyproject(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError("project version not found")
    return match.group(1)


def _add(findings: list[dict], level: str, name: str, detail: str) -> None:
    findings.append({"level": level, "name": name, "detail": detail})


def should_skip_path(path: Path) -> bool:
    return any(
        part in IGNORED_TREE_PARTS
        or part == "__pycache__"
        or part.endswith(".egg-info")
        or part.endswith(".pyc")
        for part in path.parts
    )


def check_release(root: Path) -> ReleaseCheckResult:
    root = root.resolve()
    findings: list[dict] = []
    pass_count = 0

    for relative in REQUIRED_FILES:
        if (root / relative).exists():
            pass_count += 1
        else:
            _add(findings, "FAIL", "required_file", f"missing {relative}")

    pyproject_path = root / "pyproject.toml"
    init_path = root / "src" / "mco" / "__init__.py"
    if pyproject_path.exists() and init_path.exists():
        package_version = _version_from_pyproject(pyproject_path)
        init_version = _version_from_init(init_path)
        if package_version == init_version:
            pass_count += 1
        else:
            _add(findings, "FAIL", "version_match", f"pyproject={package_version} __init__={init_version}")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8") if (root / "CHANGELOG.md").exists() else ""
        if f"## {package_version}" in changelog:
            pass_count += 1
        else:
            _add(findings, "FAIL", "changelog_version", f"CHANGELOG.md missing ## {package_version}")

    generated = []
    for path in root.rglob("*"):
        if should_skip_path(path):
            continue
        path_text = str(path)
        if any(pattern in path_text for pattern in GENERATED_PATTERNS):
            generated.append(str(path.relative_to(root)))
    if generated:
        _add(findings, "WARN", "generated_files", ", ".join(generated[:20]))
    else:
        pass_count += 1

    text_suffixes = {".py", ".md", ".json", ".toml", ".yml", ".yaml"}
    shell_true = []
    for path in root.rglob("*"):
        if should_skip_path(path) or not path.is_file() or path.suffix not in text_suffixes:
            continue
        if ("shell" + "=True") in path.read_text(encoding="utf-8"):
            shell_true.append(str(path.relative_to(root)))
    if shell_true:
        _add(findings, "FAIL", "arbitrary_shell", ", ".join(shell_true))
    else:
        pass_count += 1

    audit = audit_tree(root)
    if audit.ok:
        pass_count += 1
    else:
        _add(findings, "FAIL", "redaction_audit", "; ".join(audit.findings))

    adapter_paths = sorted((root / "templates" / "adapters").glob("*.disabled.json"))
    packaged_adapter_paths = sorted((root / "src" / "mco" / "templates" / "adapters").glob("*.disabled.json"))
    if adapter_paths and len(adapter_paths) == len(packaged_adapter_paths):
        pass_count += 1
    else:
        _add(findings, "FAIL", "adapter_template_count", "root templates and packaged templates differ")
    for path in adapter_paths + packaged_adapter_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            validate_adapter_manifest(payload)
            if payload["supervised"] or payload["can_run_shell"] or payload["can_write_artifacts"]:
                _add(findings, "FAIL", "adapter_disabled", f"{path.relative_to(root)} grants execution/write authority")
            elif payload.get("quota_status") != "unknown":
                _add(findings, "FAIL", "adapter_quota", f"{path.relative_to(root)} quota_status is not unknown")
            else:
                pass_count += 1
        except Exception as exc:
            _add(findings, "FAIL", "adapter_manifest", f"{path.relative_to(root)}: {exc}")

    if (root / ".git").exists():
        pass_count += 1
    else:
        _add(findings, "WARN", "git_repository", "not initialized")

    fail_count = sum(1 for finding in findings if finding["level"] == "FAIL")
    warn_count = sum(1 for finding in findings if finding["level"] == "WARN")
    return ReleaseCheckResult(pass_count=pass_count, warn_count=warn_count, fail_count=fail_count, findings=findings)
