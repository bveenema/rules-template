"""Secret scanning with gitleaks, plus a path allowlist for fixtures."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from lint.finding import format_finding

RULE = "secrets"
GITLEAKS_VERSION = "8.30.1"


def gitleaks_binary(root: Path) -> str | None:
    override = os.environ.get("GITLEAKS_BIN")
    if override and Path(override).is_file():
        return override
    found = shutil.which("gitleaks")
    if found:
        return found
    local = root / ".tools" / "gitleaks"
    if local.is_file():
        return str(local)
    return None


def _allowlist_paths(root: Path) -> list[str]:
    paths = [
        r"(?:^|/)tests/fixtures/",
        r"(?:^|/)__pycache__/",
        r"(?:^|/)\.git/",
        r"(?:^|/)\.tools/",
    ]
    extra = root / "config" / "gitleaks-allowlist.txt"
    if extra.is_file():
        for raw in extra.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            paths.append(line)
    return paths


def _toml_basic(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_config(root: Path, destination: Path) -> None:
    """Write a gitleaks config that extends the built-in rules."""
    quoted = ",\n".join(f"  {_toml_basic(path)}" for path in _allowlist_paths(root))
    destination.write_text(
        "\n".join(
            [
                'title = "rules-template"',
                "",
                "[extend]",
                "useDefault = true",
                "",
                "[allowlist]",
                'description = "Fixtures and project path regexes from config/gitleaks-allowlist.txt"',
                "paths = [",
                quoted,
                "]",
                "",
            ]
        ),
        encoding="utf-8",
    )


def check(root: Path) -> list[str]:
    binary = gitleaks_binary(root)
    if binary is None:
        return [
            format_finding(
                RULE,
                "",
                None,
                "gitleaks is not installed. Run scripts/install-gitleaks.sh "
                f"(pinned {GITLEAKS_VERSION}) or put the gitleaks binary on PATH, then re-run python3 -m lint.",
            )
        ]

    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "gitleaks.toml"
        report = Path(tmp) / "report.json"
        write_config(root, config)
        result = subprocess.run(
            [
                binary,
                "detect",
                "--no-git",
                "--source",
                str(root),
                "--config",
                str(config),
                "--redact",
                "--no-banner",
                "--no-color",
                "--exit-code",
                "1",
                "--report-format",
                "json",
                "--report-path",
                str(report),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return []
        if result.returncode != 1 or not report.is_file():
            detail = (result.stderr or result.stdout or "gitleaks failed").strip().splitlines()
            tail = detail[-1] if detail else "gitleaks failed"
            return [
                format_finding(
                    RULE,
                    "",
                    None,
                    f"gitleaks could not scan the tree ({tail}). Install gitleaks {GITLEAKS_VERSION} and re-run python3 -m lint.",
                )
            ]
        try:
            leaks = json.loads(report.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            return [
                format_finding(
                    RULE,
                    "",
                    None,
                    "gitleaks wrote a report that could not be read. Re-run python3 -m lint after updating gitleaks.",
                )
            ]

    findings: list[str] = []
    for leak in leaks:
        raw_path = str(leak.get("File") or "")
        try:
            rel = str(Path(raw_path).resolve().relative_to(root.resolve()))
        except ValueError:
            rel = raw_path
        rule_id = str(leak.get("RuleID") or "secret")
        line = leak.get("StartLine") or None
        findings.append(
            format_finding(
                RULE,
                rel,
                int(line) if line else None,
                f"possible secret ({rule_id}). Remove the credential and rotate it if it was real. "
                "Intentional fakes belong under tests/fixtures/ or a path regex in config/gitleaks-allowlist.txt.",
            )
        )
    return findings
