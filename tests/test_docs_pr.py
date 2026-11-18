"""Docs are required for code changes, with an opt-out marker."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from lint.rules.docs_pr import check, evaluate
from tests.support import commit_all, init_repo, run_git


class DocsEvaluateTest(unittest.TestCase):
    def test_flags_code_without_docs(self) -> None:
        findings = evaluate(["src/app.py"], [], [])
        joined = "\n".join(findings)
        self.assertIn("CHANGELOG.md", joined)
        self.assertIn("kb/", joined)
        self.assertIn("README.md", joined)
        self.assertIn("[skip-changelog]", joined)

    def test_passes_when_docs_updated(self) -> None:
        changed = ["src/app.py", "CHANGELOG.md", "kb/checks.md", "README.md"]
        self.assertEqual(evaluate(changed, [], []), [])

    def test_skip_marker_and_label(self) -> None:
        self.assertEqual(evaluate(["src/app.py"], [], ["[skip-docs] typo"]), [])
        self.assertEqual(evaluate(["src/app.py"], ["skip-docs"], []), [])

    def test_partial_marker(self) -> None:
        findings = evaluate(["lint/runner.py", "CHANGELOG.md"], [], ["[skip-kb] [skip-readme]"])
        self.assertEqual(findings, [])

    def test_markdown_only_does_not_require_docs(self) -> None:
        self.assertEqual(evaluate(["kb/index.md", "README.md"], [], []), [])


class DocsRepoTest(unittest.TestCase):
    def test_repo_diff_flags_missing_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            (root / "README.md").write_text("# demo\n", encoding="utf-8")
            commit_all(root, "base")
            run_git(root, "checkout", "-b", "feature")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            commit_all(root, "add code")
            previous = os.environ.get("LINT_BASE")
            os.environ["LINT_BASE"] = "main"
            try:
                findings, _ = check(root)
            finally:
                if previous is None:
                    os.environ.pop("LINT_BASE", None)
                else:
                    os.environ["LINT_BASE"] = previous
            self.assertTrue(any("CHANGELOG.md" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
