"""Private-info patterns, the blocklist, and clean samples."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from lint.patterns import INTERNAL_HOST
from lint.rules.private_info import NO_BLOCKLIST_NOTICE, check_files


def _ip() -> str:
    return "10" + ".1.2.3"


def _host() -> str:
    return "db" + ".internal"


def _email() -> str:
    return "ada" + "@" + "private.test"


def _url() -> str:
    return "postgres://app:" + "s3cr3t@" + _ip() + "/app"


class PrivateInfoTest(unittest.TestCase):
    def test_flags_private_ip(self) -> None:
        findings, _ = check_files([("src/net.txt", f"host = {_ip()}\n")], Path("."))
        self.assertTrue(any("private IP address" in item and "src/net.txt:1" in item for item in findings))
        self.assertTrue(any("supply the address at runtime" in item for item in findings))

    def test_flags_internal_hostname(self) -> None:
        findings, _ = check_files([("src/net.txt", f"host = {_host()}\n")], Path("."))
        self.assertTrue(any("internal-looking hostname" in item for item in findings))

    def test_ignores_filename_with_local_suffix(self) -> None:
        self.assertIsNone(INTERNAL_HOST.search("copy .claude/settings.local.json if present"))
        findings, _ = check_files([("docs/note.md", "copy settings.local.json\n")], Path("."))
        self.assertFalse(any("internal-looking hostname" in item for item in findings))

    def test_flags_email(self) -> None:
        findings, _ = check_files([("src/owner.txt", f"contact {_email()}\n")], Path("."))
        self.assertTrue(any("email address" in item and "src/owner.txt:1" in item for item in findings))
        self.assertNotIn(_email(), "\n".join(findings))

    def test_allows_example_email(self) -> None:
        findings, _ = check_files([("README.md", "contact dev@example.com\n")], Path("."))
        self.assertFalse(any("email address" in item for item in findings))

    def test_flags_connection_string(self) -> None:
        findings, _ = check_files([("src/db.txt", _url() + "\n")], Path("."))
        self.assertTrue(any("database connection string" in item for item in findings))
        self.assertNotIn("s3cr3t", "\n".join(findings))

    def test_allows_placeholder_connection_string(self) -> None:
        sample = "postgres://USER:PASSWORD@db.example.com:5432/DBNAME\n"
        findings, _ = check_files([("README.md", sample)], Path("."))
        self.assertFalse(any("database connection string" in item for item in findings))
        self.assertFalse(any("private IP address" in item for item in findings))

    def test_passes_good_sample(self) -> None:
        findings, notices = check_files([("src/app.py", "print('hello')\n")], Path("."))
        self.assertEqual(findings, [])
        self.assertIn(NO_BLOCKLIST_NOTICE, notices)

    def test_blocklist_from_env_does_not_print_the_term(self) -> None:
        term = "zz-blocklist-example-term"
        previous = os.environ.get("PRIVATE_INFO_BLOCKLIST")
        os.environ["PRIVATE_INFO_BLOCKLIST"] = f"# comment\n{term}\n"
        try:
            findings, notices = check_files([("src/app.py", f"name = {term!r}\n")], Path("."))
        finally:
            if previous is None:
                os.environ.pop("PRIVATE_INFO_BLOCKLIST", None)
            else:
                os.environ["PRIVATE_INFO_BLOCKLIST"] = previous
        self.assertTrue(any("project blocklist" in item and "src/app.py:1" in item for item in findings))
        self.assertNotIn(term, "\n".join(findings))
        self.assertNotIn(NO_BLOCKLIST_NOTICE, notices)

    def test_blocklist_from_local_file(self) -> None:
        import tempfile

        term = "yy-local-blocklist-term"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "config"
            local.mkdir()
            (local / "private-blocklist.txt").write_text(term + "\n", encoding="utf-8")
            previous = os.environ.pop("PRIVATE_INFO_BLOCKLIST", None)
            try:
                findings, notices = check_files([("src/app.py", f"uses {term}\n")], root)
            finally:
                if previous is not None:
                    os.environ["PRIVATE_INFO_BLOCKLIST"] = previous
            self.assertTrue(any("project blocklist" in item for item in findings))
            self.assertNotIn(NO_BLOCKLIST_NOTICE, notices)

    def test_notice_when_blocklist_missing(self) -> None:
        previous = os.environ.pop("PRIVATE_INFO_BLOCKLIST", None)
        try:
            _, notices = check_files([("src/app.py", "print('hello')\n")], Path("/no/such/blocklist/root"))
        finally:
            if previous is not None:
                os.environ["PRIVATE_INFO_BLOCKLIST"] = previous
        self.assertIn(NO_BLOCKLIST_NOTICE, notices)


if __name__ == "__main__":
    unittest.main()
