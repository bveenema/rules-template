"""Windows asset names for the gitleaks installer."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT

SCRIPT = ROOT / "scripts" / "install-gitleaks.sh"


def _uname(directory: Path, system: str, machine: str) -> None:
    path = directory / "uname"
    path.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                'case "$1" in',
                f"  -s) printf '%s\\n' '{system}' ;;",
                f"  -m) printf '%s\\n' '{machine}' ;;",
                "esac",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _asset(system: str, machine: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _uname(root, system, machine)
        env = os.environ.copy()
        env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            ["bash", str(SCRIPT), "--print-asset"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class WindowsAssetNameTest(unittest.TestCase):
    def test_git_bash_selects_windows_zip(self) -> None:
        cases = (
            ("MINGW64_NT-10.0", "x86_64", "gitleaks_8.30.1_windows_x64.zip"),
            ("MSYS_NT-10.0", "aarch64", "gitleaks_8.30.1_windows_arm64.zip"),
            ("CYGWIN_NT-10.0", "arm64", "gitleaks_8.30.1_windows_arm64.zip"),
            ("Linux", "x86_64", "gitleaks_8.30.1_linux_x64.tar.gz"),
        )
        for system, machine, expected in cases:
            with self.subTest(system=system, machine=machine):
                self.assertEqual(_asset(system, machine), expected)


if __name__ == "__main__":
    unittest.main()
