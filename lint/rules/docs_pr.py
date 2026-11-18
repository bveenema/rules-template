"""Require changelog, knowledge-base, and readme updates when code changes.

Opt out with a PR label or a marker in the PR body or a commit message:
  [skip-docs] skips all three
  [skip-changelog] [skip-kb] [skip-readme] skip one
Labels use the same names without brackets: skip-docs, skip-changelog, skip-kb, skip-readme.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from lint.finding import format_finding

RULE = "docs"

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".cs",
    ".kt",
    ".sh",
    ".bash",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
}
CODE_DIRS = ("lint/", "rules/", "scripts/", "tests/", ".githooks/", ".github/", "config/")

_MESSAGES = {
    "changelog": (
        "CHANGELOG.md",
        "code changed but CHANGELOG.md was not updated. Add an entry, or add [skip-changelog] "
        "to the commit message or PR body (or the skip-changelog label) when a changelog entry is not appropriate.",
    ),
    "kb": (
        "kb/",
        "code changed but no file under kb/ was updated. Update the knowledge base, or add [skip-kb] "
        "when a knowledge-base update is not appropriate.",
    ),
    "readme": (
        "README.md",
        "code changed but README.md was not updated. Update the readme, or add [skip-readme] "
        "when a readme update is not appropriate.",
    ),
}


def is_code_path(path: str) -> bool:
    rel = path.replace("\\", "/")
    if rel.endswith(".md") or rel.endswith(".example"):
        return False
    suffix = Path(rel).suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return True
    return rel.startswith(CODE_DIRS)


_LINE_MARKERS = ("[skip-docs]", "[skip-changelog]", "[skip-kb]", "[skip-readme]")


def markers_in_text(text: str) -> set[str]:
    """Markers count only as the first token of a line, or as a line of markers.

    A sentence that mentions the marker, including this repository's own docs,
    does not opt out.
    """
    found: set[str] = set()
    known = set(_LINE_MARKERS)
    for raw in text.splitlines():
        parts = raw.strip().split()
        if not parts or parts[0] not in known:
            continue
        if all(part in known for part in parts):
            found.update(parts)
        else:
            found.add(parts[0])
    return found


def markers_from(labels: list[str], texts: list[str]) -> dict[str, bool]:
    label_set = {label.strip().lower() for label in labels if label.strip()}
    text_markers: set[str] = set()
    for text in texts:
        text_markers.update(markers_in_text(text))
    skip_all = "skip-docs" in label_set or "[skip-docs]" in text_markers
    return {
        "changelog": skip_all or "skip-changelog" in label_set or "[skip-changelog]" in text_markers,
        "kb": skip_all or "skip-kb" in label_set or "[skip-kb]" in text_markers,
        "readme": skip_all or "skip-readme" in label_set or "[skip-readme]" in text_markers,
    }


def evaluate(changed: list[str], labels: list[str], texts: list[str]) -> list[str]:
    if not any(is_code_path(path) for path in changed):
        return []
    normalized = [path.replace("\\", "/") for path in changed]
    present = {
        "changelog": any(path == "CHANGELOG.md" for path in normalized),
        "kb": any(path.startswith("kb/") and path.endswith(".md") for path in normalized),
        "readme": any(path == "README.md" for path in normalized),
    }
    skipped = markers_from(labels, texts)
    findings: list[str] = []
    for key, (where, message) in _MESSAGES.items():
        if present[key] or skipped[key]:
            continue
        findings.append(format_finding(RULE, where, None, message))
    return findings


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _ref_exists(root: Path, ref: str) -> bool:
    return _git(root, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def resolve_base(root: Path) -> str | None:
    override = os.environ.get("LINT_BASE", "").strip()
    if override:
        return override
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base:
        return f"origin/{github_base}"
    for candidate in ("origin/main", "origin/master", "main", "master"):
        if _ref_exists(root, candidate):
            return candidate
    return None


def _changed_paths(root: Path, base: str) -> list[str] | None:
    merge_base = _git(root, "merge-base", base, "HEAD")
    if merge_base.returncode != 0:
        return None
    base_sha = merge_base.stdout.strip()
    names: set[str] = set()
    for args in (
        ["diff", "--name-only", base_sha],
        ["diff", "--name-only", "--cached", base_sha],
    ):
        result = _git(root, *args)
        if result.returncode != 0:
            return None
        names.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    if untracked.returncode == 0:
        names.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return sorted(names)


def _commit_messages(root: Path, base: str) -> list[str]:
    merge_base = _git(root, "merge-base", base, "HEAD")
    if merge_base.returncode != 0:
        return []
    log = _git(root, "log", "--format=%B%x1e", f"{merge_base.stdout.strip()}..HEAD")
    if log.returncode != 0:
        return []
    return [part.strip() for part in log.stdout.split("\x1e") if part.strip()]


def _github_metadata() -> tuple[list[str], str]:
    labels: list[str] = []
    body = ""
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if event_path and Path(event_path).is_file():
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        pull = payload.get("pull_request") or {}
        body = pull.get("body") or ""
        labels.extend(item.get("name", "") for item in pull.get("labels") or [] if isinstance(item, dict))
    extra = os.environ.get("PR_LABELS", "")
    labels.extend(part.strip() for part in extra.split(",") if part.strip())
    body = "\n".join(part for part in (body, os.environ.get("PR_BODY", "")) if part)
    return labels, body


def check(root: Path) -> tuple[list[str], list[str]]:
    base = resolve_base(root)
    if base is None or not _ref_exists(root, base):
        message = (
            "docs: could not find a base ref to compare. Set LINT_BASE to the branch this change "
            "merges into (for example origin/main) and re-run python3 -m lint."
        )
        if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("LINT_DOCS_REQUIRED") == "1":
            return [message], []
        return [], [message + " Skipped the docs check outside CI."]
    changed = _changed_paths(root, base)
    if changed is None:
        return [
            format_finding(
                RULE,
                "",
                None,
                f"could not diff against {base}. Fetch the base branch and re-run python3 -m lint.",
            )
        ], []
    labels, body = _github_metadata()
    texts = _commit_messages(root, base)
    if body:
        texts.append(body)
    pending = os.environ.get("LINT_COMMIT_MSG", "")
    if pending:
        texts.append(pending)
    return evaluate(changed, labels, texts), []
