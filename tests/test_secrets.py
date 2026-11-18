"""Gitleaks flags a bad sample, passes a clean file, and ignores fixtures."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from lint.rules.secrets import check, gitleaks_binary
from tests.support import ROOT


def _token() -> str:
    return "xoxb-" + "123456789012" + "-" + "123456789012" + "-" + "abcdefghijklmnopqrstuvwx"


class SecretsTest(unittest.TestCase):
    def setUp(self) -> None:
        binary = ROOT / ".tools" / "gitleaks"
        if not binary.is_file():
            self.skipTest("gitleaks is not installed; run scripts/install-gitleaks.sh")
        self._previous = os.environ.get("GITLEAKS_BIN")
        os.environ["GITLEAKS_BIN"] = str(binary)

    def tearDown(self) -> None:
        if self._previous is None:
            os.environ.pop("GITLEAKS_BIN", None)
        else:
            os.environ["GITLEAKS_BIN"] = self._previous

    def test_flags_bad_sample(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = _token()
            (root / "src").mkdir()
            (root / "src" / "app.env").write_text(f"token={token}\n", encoding="utf-8")
            findings = check(root)
            self.assertTrue(findings, "expected a secret finding")
            self.assertIn("src/app.env", findings[0])
            self.assertIn("Remove the credential", findings[0])
            self.assertNotIn(token, "\n".join(findings))

    def test_passes_good_sample(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.txt").write_text("token = 'not-a-secret'\n", encoding="utf-8")
            self.assertEqual(check(root), [])

    def test_allowlist_ignores_fixture(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = _token()
            dest = root / "tests" / "fixtures"
            dest.mkdir(parents=True)
            (dest / "sample.env").write_text(f"token={token}\n", encoding="utf-8")
            self.assertEqual(check(root), [])


class GitleaksExeTest(unittest.TestCase):
    def test_finds_gitleaks_exe_in_tools(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / ".tools" / "gitleaks.exe"
            exe.parent.mkdir()
            exe.write_bytes(b"")
            previous_bin = os.environ.pop("GITLEAKS_BIN", None)
            previous_path = os.environ.get("PATH")
            os.environ["PATH"] = "/usr/bin:/bin"
            try:
                found = gitleaks_binary(root)
            finally:
                if previous_bin is None:
                    os.environ.pop("GITLEAKS_BIN", None)
                else:
                    os.environ["GITLEAKS_BIN"] = previous_bin
                if previous_path is None:
                    os.environ.pop("PATH", None)
                else:
                    os.environ["PATH"] = previous_path
            self.assertEqual(found, str(exe))


if __name__ == "__main__":
    unittest.main()
