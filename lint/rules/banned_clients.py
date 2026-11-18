"""Forbidden database clients and connection-string fragments.

The list lives in the committed file config/banned-clients.txt. The template
ships that file with no active patterns, so a new project is not blocked until
it chooses its own list.
"""

from __future__ import annotations

from pathlib import Path

from lint.finding import format_finding

RULE = "banned-clients"
CONFIG = Path("config") / "banned-clients.txt"


def load_patterns(root: Path) -> list[str]:
    path = root / CONFIG
    if not path.is_file():
        return []
    patterns: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def check(root: Path, files: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    path = root / CONFIG
    if not path.is_file():
        return [
            format_finding(
                RULE,
                str(CONFIG),
                None,
                "config file is missing. Create it and list one forbidden literal per line. "
                "An empty file turns the rule off.",
            )
        ], []
    patterns = load_patterns(root)
    if not patterns:
        return [], []
    config_rel = str(CONFIG).replace("\\", "/")
    findings: list[str] = []
    for rel, text in files:
        if rel.replace("\\", "/") == config_rel:
            continue
        for pattern in patterns:
            start = 0
            while True:
                at = text.find(pattern, start)
                if at < 0:
                    break
                line = text.count("\n", 0, at) + 1
                findings.append(
                    format_finding(
                        RULE,
                        rel,
                        line,
                        f"forbidden database client or connection pattern {pattern!r}. "
                        "Remove it and use the client this project allows. The list is config/banned-clients.txt.",
                    )
                )
                start = at + len(pattern)
    return findings, []
