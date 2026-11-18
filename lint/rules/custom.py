"""Load project rules from rules/*.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from lint.finding import format_finding

RULE = "custom"


def _modules(root: Path) -> list[tuple[Path, object]]:
    rules_dir = root / "rules"
    if not rules_dir.is_dir():
        return []
    loaded: list[tuple[Path, object]] = []
    for path in sorted(rules_dir.glob("*.py")):
        name = path.name
        if name.startswith("_") or name.startswith("test_") or name.endswith("_test.py"):
            continue
        spec = importlib.util.spec_from_file_location(f"project_rule_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded.append((path, module))
    return loaded


def check(root: Path, files: list[tuple[str, str]]) -> list[str]:
    findings: list[str] = []
    try:
        modules = _modules(root)
    except Exception as exc:  # a broken project rule should fail the run, not crash it
        return [
            format_finding(
                RULE,
                "rules",
                None,
                f"could not load a project rule ({type(exc).__name__}: {exc}). "
                "Each rules/*.py module must import cleanly and define check(files).",
            )
        ]
    for path, module in modules:
        rel = str(path.relative_to(root))
        check_fn = getattr(module, "check", None)
        if not callable(check_fn):
            findings.append(
                format_finding(
                    RULE,
                    rel,
                    None,
                    "rule module must define check(files) and return a list of failure messages. "
                    "Copy rules/example_forbidden_token.py and keep that function.",
                )
            )
            continue
        try:
            result = check_fn(files)
        except Exception as exc:
            findings.append(
                format_finding(
                    RULE,
                    rel,
                    None,
                    f"check(files) raised {type(exc).__name__}: {exc}. Return a list of messages instead.",
                )
            )
            continue
        if not isinstance(result, list) or any(not isinstance(item, str) for item in result):
            findings.append(
                format_finding(
                    RULE,
                    rel,
                    None,
                    "check(files) must return a list of strings. See rules/example_forbidden_token.py.",
                )
            )
            continue
        findings.extend(result)
    return findings
