"""Template sync updates shared rules and keeps project config."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT, init_repo


def _load():
    path = ROOT / "scripts" / "sync-from-template.py"
    spec = importlib.util.spec_from_file_location("sync_from_template", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load sync script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncTest(unittest.TestCase):
    def test_keeps_project_config_and_updates_runner(self) -> None:
        module = _load()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            init_repo(dest)
            banned = dest / "config"
            banned.mkdir()
            (banned / "banned-clients.txt").write_text("project-specific-driver\n", encoding="utf-8")
            (dest / "rules").mkdir()
            (dest / "rules" / "keep_me.py").write_text("keep this rule\n", encoding="utf-8")
            (dest / "lint").mkdir()
            (dest / "lint" / "runner.py").write_text("old runner\n", encoding="utf-8")
            (dest / "AGENTS.md").write_text(
                "# AGENTS.md\n\n## Local\n\nKeep this section.\n\n"
                "<!-- rules-template:house-rules:start -->\nold rules\n"
                "<!-- rules-template:house-rules:end -->\n",
                encoding="utf-8",
            )
            lines = module.sync(ROOT, dest, dry_run=False)
            self.assertIn("kept project file: config/banned-clients.txt", lines)
            self.assertEqual((dest / "config" / "banned-clients.txt").read_text(encoding="utf-8"), "project-specific-driver\n")
            self.assertEqual((dest / "rules" / "keep_me.py").read_text(encoding="utf-8"), "keep this rule\n")
            self.assertEqual(
                (dest / "lint" / "runner.py").read_text(encoding="utf-8"),
                (ROOT / "lint" / "runner.py").read_text(encoding="utf-8"),
            )
            agents = (dest / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep this section.", agents)
            self.assertIn("python3 -m lint", agents)
            self.assertNotIn("old rules", agents)
            self.assertTrue(any("AGENTS.md house-rules" in line for line in lines))

    def test_refuses_to_overwrite_banned_clients_even_if_marked_sync(self) -> None:
        module = _load()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / "config").mkdir()
            (dest / "config" / "banned-clients.txt").write_text("keep\n", encoding="utf-8")
            message = module._apply_one(ROOT, dest, "sync", "config/banned-clients.txt", False)
            self.assertIn("kept project file", message)
            self.assertEqual((dest / "config" / "banned-clients.txt").read_text(encoding="utf-8"), "keep\n")

    def test_dry_run_writes_nothing(self) -> None:
        module = _load()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            lines = module.sync(ROOT, dest, dry_run=True)
            self.assertFalse((dest / "lint" / "runner.py").exists())
            self.assertTrue(any(line.startswith("would update") for line in lines))

    def test_cli_rejects_https_fallback_message(self) -> None:
        # A local source is the supported offline path. A missing URL must not
        # be rewritten; the clone error stays on stderr/stdout from git.
        script = ROOT / "scripts" / "sync-from-template.py"
        text = script.read_text(encoding="utf-8")
        self.assertIn("git@github.com:bveenema/rules-template.git", text)
        self.assertIn("does not fall back to HTTPS", text)
        self.assertNotIn("https://github.com", text)


if __name__ == "__main__":
    unittest.main()
