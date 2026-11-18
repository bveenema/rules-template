"""The template itself passes the checks it ships."""

from __future__ import annotations

import subprocess
import sys
import unittest

from tests.support import ROOT


class RepoCleanTest(unittest.TestCase):
    def test_lint_passes_on_this_repo(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "lint"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
