"""Helpers for lint tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Test User"
    env["GIT_AUTHOR_EMAIL"] = "dev@example.com"
    env["GIT_COMMITTER_NAME"] = "Test User"
    env["GIT_COMMITTER_EMAIL"] = "dev@example.com"
    return env


def run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, env=git_env(), capture_output=True, text=True)


def init_repo(root: Path) -> None:
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.name", "Test User")
    run_git(root, "config", "user.email", "dev@example.com")


def commit_all(root: Path, message: str) -> None:
    run_git(root, "add", "-A")
    run_git(root, "commit", "-m", message)
