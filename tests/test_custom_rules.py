"""The runner loads the example rule and ignores its test module."""

from __future__ import annotations

import unittest

from lint.rules.custom import check
from rules.example_forbidden_token import TOKEN
from tests.support import ROOT


class CustomRulesTest(unittest.TestCase):
    def test_repo_example_passes(self) -> None:
        self.assertEqual(check(ROOT, [("src/app.py", "print('hello')\n")]), [])

    def test_example_flags_bad_sample_via_loader(self) -> None:
        findings = check(ROOT, [("src/app.py", f"value = {TOKEN}\n")])
        self.assertEqual(len(findings), 1)
        self.assertIn("src/app.py:1", findings[0])
        self.assertIn("Remove it", findings[0])

    def test_example_passes_good_sample_via_loader(self) -> None:
        self.assertEqual(check(ROOT, [("src/app.py", "value = 'ready'\n")]), [])


if __name__ == "__main__":
    unittest.main()
