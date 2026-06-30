from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_PATTERNS = [
    "/" + "Users" + "/" + "liuyang",
    "AI" + "-Agent" + "-Vault",
    "20260623" + "-142151-demo",
    "h" + "dl-",
    "海" + "底" + "捞",
    "杭州" + "西湖" + "店",
    "nacos" + "-program",
    "superapp" + "-inner",
    "h" + "dltest",
]

CHECKED_SUFFIXES = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".html"}


@dataclass(frozen=True)
class AuditResult:
    pass_count: int
    warn_count: int
    fail_count: int
    findings: list[str]

    @property
    def ok(self) -> bool:
        return self.fail_count == 0


def audit_tree(root: Path) -> AuditResult:
    findings: list[str] = []
    pass_count = 0
    for path in root.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.suffix not in CHECKED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                findings.append(f"{path.relative_to(root)} contains forbidden pattern: {pattern}")
        pass_count += 1
    return AuditResult(pass_count=pass_count, warn_count=0, fail_count=len(findings), findings=findings)
