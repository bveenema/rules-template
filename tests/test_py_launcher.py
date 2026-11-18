"""scripts/py picks the first real Python 3.9+ on PATH."""

from __future__ import annotations

import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT

LAUNCHER = ROOT / "scripts" / "py"


def _fake(directory: Path, name: str, probe_exit: int, identity: str) -> None:
    path = directory / name
    path.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                'printf "%s\\n" "$*" >> "$OUT"',
                'case "$*" in',
                f"  *version_info*) exit {probe_exit} ;;",
                "esac",
                f'printf "%s\\n" "{identity}"',
                "exit 0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run(bin_dir: Path, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {"PATH": str(bin_dir), "OUT": str(out), "HOME": str(bin_dir)}
    return subprocess.run(
        ["/bin/sh", str(LAUNCHER), *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class PyLauncherTest(unittest.TestCase):
    def test_only_python_selects_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            _fake(root, "python", 0, "TOKEN_A_PYTHON")
            result = _run(root, out, "-c", "print(1)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TOKEN_A_PYTHON", result.stdout)
            self.assertNotIn("TOKEN_B_PY", result.stdout)

    def test_only_py_selects_py_dash_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            _fake(root, "py", 0, "TOKEN_B_PY")
            result = _run(root, out, "-c", "print(1)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TOKEN_B_PY", result.stdout)
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertTrue(lines, "launcher never invoked py")
            self.assertTrue(all(line.startswith("-3 ") for line in lines), lines)

    def test_python2_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            _fake(root, "python", 1, "TOKEN_A_PYTHON")
            result = _run(root, out, "-c", "print(1)")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("TOKEN_A_PYTHON", result.stdout)
            self.assertIn("Python 3.9", result.stderr)
            self.assertIn("py -3", result.stderr)

    def test_python2_falls_through_to_py(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            _fake(root, "python", 1, "TOKEN_A_PYTHON")
            _fake(root, "py", 0, "TOKEN_B_PY")
            result = _run(root, out, "-c", "print(1)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TOKEN_B_PY", result.stdout)
            self.assertNotIn("TOKEN_A_PYTHON", result.stdout)

    def test_python3_wins_over_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            _fake(root, "python3", 0, "TOKEN_C_PYTHON3")
            _fake(root, "python", 0, "TOKEN_A_PYTHON")
            result = _run(root, out, "-c", "print(1)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TOKEN_C_PYTHON3", result.stdout)
            self.assertNotIn("TOKEN_A_PYTHON", result.stdout)

    def test_none_fails_with_install_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty = root / "empty"
            empty.mkdir()
            out = root / "out"
            result = _run(empty, out, "-c", "print(1)")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no Python 3.9", result.stderr)
            self.assertIn("https://www.python.org/downloads/", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_hooks_and_ci_call_the_launcher(self) -> None:
        for rel in (
            ".githooks/pre-commit",
            ".githooks/commit-msg",
            "lefthook.yml",
            ".github/workflows/lint.yml",
        ):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("sh scripts/py", text, rel)
            self.assertNotIn("python3", text, rel)


if __name__ == "__main__":
    unittest.main()
