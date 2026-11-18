"""The example rule flags a bad sample and passes a good one."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rules.example_forbidden_token import TOKEN, check


class ExampleForbiddenTokenTest(unittest.TestCase):
    def test_flags_bad_sample(self) -> None:
        findings = check([("src/app.py", f"note = {TOKEN!r}\n")])
        self.assertEqual(len(findings), 1)
        self.assertIn("src/app.py:1", findings[0])
        self.assertIn("Remove it", findings[0])

    def test_passes_good_sample(self) -> None:
        self.assertEqual(check([("src/app.py", "note = 'ready'\n")]), [])

    def test_ignores_its_own_source(self) -> None:
        self.assertEqual(check([("rules/example_forbidden_token.py", f"TOKEN = {TOKEN!r}\n")]), [])


if __name__ == "__main__":
    unittest.main()
