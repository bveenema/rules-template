"""Read the text that git will commit."""

from __future__ import annotations

import subprocess
from pathlib import Path

MAX_BYTES = 1_000_000


def repo_root(start: Path | None = None) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start or Path.cwd()), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "not a git repository")
    return Path(result.stdout.strip())


def _listed(root: Path, *args: str) -> list[str]:
    listed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=True,
    )
    return [item.decode("utf-8", "surrogateescape") for item in listed.stdout.split(b"\0") if item]


def _read_worktree(root: Path, path: str) -> str | None:
    disk = root / path
    if not disk.is_file():
        return None
    data = disk.read_bytes()
    if len(data) > MAX_BYTES or b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", "replace")


def load_indexed_files(root: Path) -> list[tuple[str, str]]:
    """Return text for staged files and for untracked files that are not ignored.

    Staged content is what a commit will record. Untracked files are included
    so `sh scripts/py -m lint` sees new files before `git add`. When the worktree
    copy of a staged file differs, both copies are checked.
    """
    tracked = _listed(root, "ls-files", "-z")
    untracked = _listed(root, "ls-files", "--others", "--exclude-standard", "-z")
    files = _blobs(root, tracked)
    staged = {path: text for path, text in files}
    for path in tracked:
        text = _read_worktree(root, path)
        if text is not None and staged.get(path) != text:
            files.append((path, text))
    for path in untracked:
        text = _read_worktree(root, path)
        if text is not None:
            files.append((path, text))
    return files


def _blobs(root: Path, paths: list[str]) -> list[tuple[str, str]]:
    if not paths:
        return []

    proc = subprocess.Popen(
        ["git", "-C", str(root), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert proc.stdin is not None and proc.stdout is not None
    for path in paths:
        proc.stdin.write(b":" + path.encode("utf-8", "surrogateescape") + b"\n")
    proc.stdin.close()

    files: list[tuple[str, str]] = []
    for path in paths:
        header = proc.stdout.readline()
        if not header or b" missing" in header:
            continue
        parts = header.split()
        if len(parts) < 3 or parts[1] != b"blob":
            continue
        size = int(parts[2])
        data = proc.stdout.read(size)
        newline = proc.stdout.read(1)
        if newline not in (b"\n", b""):
            break
        if size > MAX_BYTES or b"\0" in data[:8192]:
            continue
        files.append((path, data.decode("utf-8", "replace")))
    proc.wait()
    return files
