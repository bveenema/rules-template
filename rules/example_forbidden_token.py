"""Example project rule. Copy this file to add your own.

Contract:
  - A rules/*.py module (not test_*.py) is loaded by `python3 -m lint`.
  - Define check(files) -> list[str].
  - files is a list of (repo-relative path, text) for indexed text files.
  - Each string is a failure line: "<name>: <path>:<line>: <what>. <how to fix>."
  - Return [] when the tree passes.

This example forbids a token that normal code will never contain. It does not
flag its own source or its test, so the template stays green.
"""

from __future__ import annotations

NAME = "example-forbidden-token"
TOKEN = "PROJECT_RULE_EXAMPLE_FORBIDDEN"
OWN = {
    "rules/example_forbidden_token.py",
    "rules/test_example_forbidden_token.py",
}


def check(files: list[tuple[str, str]]) -> list[str]:
    findings: list[str] = []
    for path, text in files:
        rel = path.replace("\\", "/")
        if rel in OWN:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if TOKEN in line:
                findings.append(
                    f"{NAME}: {rel}:{line_number}: found {TOKEN}. "
                    "Remove it. Copy rules/example_forbidden_token.py to a new name under rules/ "
                    "and change TOKEN to enforce a real project rule."
                )
    return findings
