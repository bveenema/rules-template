"""Banned-client patterns are off until a project lists one."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lint.rules.banned_clients import check


class BannedClientsTest(unittest.TestCase):
    def test_flags_configured_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            pattern = "example-db-driver"
            (config / "banned-clients.txt").write_text(f"# note\n{pattern}\n", encoding="utf-8")
            findings, _ = check(root, [("src/db.py", f"import {pattern}\n")])
            self.assertEqual(len(findings), 1)
            self.assertIn("src/db.py:1", findings[0])
            self.assertIn(pattern, findings[0])
            self.assertIn("config/banned-clients.txt", findings[0])

    def test_passes_clean_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            (config / "banned-clients.txt").write_text("example-db-driver\n", encoding="utf-8")
            findings, _ = check(root, [("src/db.py", "import sqlite3\n")])
            self.assertEqual(findings, [])

    def test_passes_when_config_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            (config / "banned-clients.txt").write_text("# no active patterns\n", encoding="utf-8")
            findings, _ = check(root, [("src/db.py", "import example-db-driver\n")])
            self.assertEqual(findings, [])

    def test_does_not_flag_the_config_file_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            (config / "banned-clients.txt").write_text("example-db-driver\n", encoding="utf-8")
            findings, _ = check(root, [("config/banned-clients.txt", "example-db-driver\n")])
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
