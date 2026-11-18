"""Run the built-in rules and any project rules under rules/."""

from __future__ import annotations  # Python 3.9 evaluates annotations later.

import sys
from pathlib import Path

from lint.files import load_indexed_files, repo_root
from lint.rules import banned_clients, custom, docs_pr, hephaestus, private_info, secrets

RULES = (
    "secrets",
    "private-info",
    "banned-clients",
    "docs",
    "hephaestus",
    "custom",
)


def _usage() -> str:
    names = " ".join(RULES)
    return (
        "Usage: sh scripts/py -m lint [rule ...]\n"
        f"Rules: {names}\n"
        "With no arguments, every rule runs.\n"
    )


def run(root: Path, selected: list[str]) -> tuple[list[str], list[str]]:
    files = load_indexed_files(root)
    findings: list[str] = []
    notices: list[str] = []
    if "secrets" in selected:
        findings.extend(secrets.check(root))
    if "private-info" in selected:
        found, notes = private_info.check_files(files, root)
        findings.extend(found)
        notices.extend(notes)
    if "banned-clients" in selected:
        found, notes = banned_clients.check(root, files)
        findings.extend(found)
        notices.extend(notes)
    if "docs" in selected:
        found, notes = docs_pr.check(root)
        findings.extend(found)
        notices.extend(notes)
    if "hephaestus" in selected:
        findings.extend(hephaestus.check(root))
    if "custom" in selected:
        findings.extend(custom.check(root, files))
    return findings, notices


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in {"-h", "--help"} for arg in args):
        sys.stdout.write(_usage())
        return 0
    unknown = [arg for arg in args if arg not in RULES]
    if unknown:
        sys.stderr.write(f"Unknown rule: {', '.join(unknown)}\n{_usage()}")
        return 2
    try:
        root = repo_root()
    except RuntimeError as exc:
        sys.stderr.write(f"lint: {exc}\n")
        return 2
    selected = args or list(RULES)
    findings, notices = run(root, selected)
    for notice in notices:
        sys.stderr.write(notice + "\n")
    for finding in findings:
        sys.stdout.write(finding + "\n")
    return 1 if findings else 0
