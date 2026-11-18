#!/usr/bin/env python3
"""Pull rule and config updates from the template into an existing repo.

Project-owned files are not overwritten. The blocklist, the banned-client
list, and the gitleaks and email allowlists stay as the project left them.
Custom rules under rules/ are left alone except for the example rule, which
the template owns.

Usage:
  python3 scripts/sync-from-template.py [--source URL-or-path] [--dest PATH] [--dry-run]

The default source is git@github.com:bveenema/rules-template.git. Pass a
local checkout with --source to try a sync without cloning.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SOURCE = "git@github.com:bveenema/rules-template.git"
START = "<!-- rules-template:house-rules:start -->"
END = "<!-- rules-template:house-rules:end -->"

# These paths stay project-owned even if a future manifest marks them sync.
NEVER_OVERWRITE = {
    "config/banned-clients.txt",
    "config/gitleaks-allowlist.txt",
    "config/email-allowlist.txt",
    "config/private-blocklist.txt",
    "CHANGELOG.md",
    "README.md",
    "kb/index.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".heph-manifest",
    ".gitignore",
}

SKIP_NAMES = {"__pycache__", ".DS_Store"}


def _parse_manifest(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        mode, rel = line.split(None, 1)
        if mode not in {"sync", "init"}:
            raise SystemExit(f"template-sync.txt: unknown mode {mode!r} on {rel}")
        rel = rel.strip().replace("\\", "/")
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise SystemExit(f"template-sync.txt: refusing path {rel}")
        entries.append((mode, rel))
    return entries


def _copy_file(src: Path, dest: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _copy_tree(src: Path, dest: Path, dry_run: bool) -> int:
    copied = 0
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [name for name in dirnames if name not in SKIP_NAMES]
        rel_dir = Path(dirpath).relative_to(src)
        for name in filenames:
            if name in SKIP_NAMES or name.endswith(".pyc"):
                continue
            _copy_file(Path(dirpath) / name, dest / rel_dir / name, dry_run)
            copied += 1
    return copied


def _apply_one(source: Path, dest_root: Path, mode: str, rel: str, dry_run: bool) -> str:
    src = source / rel
    dest = dest_root / rel
    if not src.exists():
        return f"missing in template: {rel}"
    if rel in NEVER_OVERWRITE:
        mode = "init"
    if mode == "init" and dest.exists():
        return f"kept project file: {rel}"
    if src.is_dir():
        count = _copy_tree(src, dest, dry_run)
        return f"{'would update' if dry_run else 'updated'} {rel}/ ({count} files)"
    _copy_file(src, dest, dry_run)
    return f"{'would update' if dry_run else 'updated'} {rel}"


def _apply_agents(source: Path, dest_root: Path, dry_run: bool) -> str:
    snippet_path = source / "template" / "agents-house-rules.md"
    if not snippet_path.is_file():
        return "template has no template/agents-house-rules.md; left AGENTS.md unchanged"
    snippet = snippet_path.read_text(encoding="utf-8").strip() + "\n"
    if START not in snippet or END not in snippet:
        return "house-rules snippet is missing its markers; left AGENTS.md unchanged"
    agents = dest_root / "AGENTS.md"
    if not agents.exists():
        text = "# AGENTS.md\n\n" + snippet
        action = "would add" if dry_run else "added"
    else:
        current = agents.read_text(encoding="utf-8")
        if START in current and END in current:
            before, rest = current.split(START, 1)
            _, after = rest.split(END, 1)
            text = before + snippet + after.lstrip("\n")
            action = "would update" if dry_run else "updated"
        else:
            sep = "" if current.endswith("\n") else "\n"
            text = current + sep + "\n" + snippet
            action = "would append" if dry_run else "appended"
    if not dry_run:
        agents.write_text(text, encoding="utf-8")
    return f"{action} AGENTS.md house-rules section"


def sync(source: Path, dest_root: Path, dry_run: bool) -> list[str]:
    manifest = source / "template-sync.txt"
    if not manifest.is_file():
        raise SystemExit(f"No template-sync.txt in {source}")
    if source.resolve() == dest_root.resolve():
        raise SystemExit("Refusing to sync a repository onto itself. Pass a different --dest.")
    lines = [_apply_one(source, dest_root, mode, rel, dry_run) for mode, rel in _parse_manifest(manifest)]
    lines.append(_apply_agents(source, dest_root, dry_run))
    return lines


def _clone(url: str) -> tempfile.TemporaryDirectory[str]:
    tmp = tempfile.TemporaryDirectory(prefix="rules-template-")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, tmp.name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        tmp.cleanup()
        detail = (result.stderr or result.stdout or "git clone failed").strip()
        raise SystemExit(
            "Could not clone the template over SSH.\n"
            f"  {url}\n"
            f"  {detail}\n"
            "Pass --source with a local checkout, or fix SSH access to that repository. "
            "This script does not fall back to HTTPS."
        )
    return tmp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync rule updates from the template.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="SSH URL or local path of the template")
    parser.add_argument("--dest", default=".", help="Repository to update")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    args = parser.parse_args(argv)
    dest = Path(args.dest).resolve()
    if not (dest / ".git").exists():
        raise SystemExit(f"{dest} is not a git checkout.")
    source_path = Path(args.source)
    cloned: tempfile.TemporaryDirectory[str] | None = None
    if source_path.exists():
        source = source_path.resolve()
    else:
        cloned = _clone(args.source)
        source = Path(cloned.name)
    try:
        for line in sync(source, dest, args.dry_run):
            print(line)
    finally:
        if cloned is not None:
            cloned.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
