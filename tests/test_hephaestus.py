"""The manifest must point at bveenema/hephaestus and list real files."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from lint.rules import hephaestus
from tests.support import ROOT


def _write(root: Path, source: str, listed: str = ".cursor/commands/ship.md") -> None:
    (root / ".cursor" / "commands").mkdir(parents=True)
    (root / listed).write_text("ship\n", encoding="utf-8")
    (root / ".heph-manifest").write_text(
        "\n".join(
            [
                "# hephaestus vendor install — regenerate with install.sh",
                "# version: 2.2.0",
                f"# source: {source}",
                listed,
                "",
            ]
        ),
        encoding="utf-8",
    )


class HephaestusTest(unittest.TestCase):
    def test_passes_bveenema_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "git@github.com:bveenema/hephaestus.git@aa504e34")
            self.assertEqual(hephaestus.check(root), [])

    def test_flags_other_fork(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            other = "git@github.com:" + hephaestus.FORBIDDEN_SLUG + ".git@abc1234"
            _write(root, other)
            findings = hephaestus.check(root)
            self.assertTrue(any("bveenema/hephaestus" in item for item in findings))
            self.assertTrue(any("different fork" in item for item in findings))

    def test_flags_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".heph-manifest").write_text(
                "# hephaestus vendor install — regenerate with install.sh\n"
                "# source: git@github.com:bveenema/hephaestus.git@aa504e34\n"
                "missing/file.md\n",
                encoding="utf-8",
            )
            findings = hephaestus.check(root)
            self.assertTrue(any("missing/file.md" in item for item in findings))

    def test_flags_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            findings = hephaestus.check(Path(tmp))
            self.assertTrue(any("manifest is missing" in item for item in findings))

    def test_this_repo_is_pinned(self) -> None:
        findings = hephaestus.check(ROOT)
        self.assertEqual(findings, [])
        text = (ROOT / ".heph-manifest").read_text(encoding="utf-8")
        self.assertIn("git@github.com:bveenema/hephaestus.git@", text)

    def test_pin_script_rewrites_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            manifest = root / ".heph-manifest"
            manifest.write_text(
                "# hephaestus vendor install — regenerate with install.sh\n"
                "# source: /tmp/local-checkout@abc1234\n"
                ".cursor/commands/ship.md\n",
                encoding="utf-8",
            )
            script = ROOT / "scripts" / "pin-hephaestus-source.sh"
            subprocess.run(["bash", str(script), "aa504e34d91cad8c577c0745e3d0de2eabf65209"], cwd=root, check=True)
            pinned = manifest.read_text(encoding="utf-8")
            self.assertIn(
                "# source: git@github.com:bveenema/hephaestus.git@aa504e34d91cad8c577c0745e3d0de2eabf65209",
                pinned,
            )
            self.assertNotIn("/tmp/local-checkout", pinned)


if __name__ == "__main__":
    unittest.main()
