"""Generic private-information patterns plus an optional project blocklist.

The blocklist is never committed. It is read from the PRIVATE_INFO_BLOCKLIST
environment variable (Cursor cloud agents and the CI secret) and from the
git-ignored file config/private-blocklist.txt (humans).
"""

from __future__ import annotations

import os
from pathlib import Path

from lint.finding import format_finding
from lint.patterns import (
    ADO_HINT,
    ADO_PASSWORD,
    DB_URL,
    EMAIL,
    INTERNAL_HOST,
    PRIVATE_IPV4,
    PRIVATE_IPV6,
    email_domain_allowed,
    is_placeholder_secret,
    line_number,
)

RULE = "private-info"
LOCAL_BLOCKLIST = Path("config") / "private-blocklist.txt"
MIN_TERM = 3

NO_BLOCKLIST_NOTICE = (
    "private-info: no project blocklist is configured. Set the PRIVATE_INFO_BLOCKLIST "
    "environment variable or create config/private-blocklist.txt (git-ignored). "
    "Generic patterns still ran. The pre-commit hook is the real guard. CI is only a "
    "backstop: it runs after push, and fork pull requests do not receive secrets."
)


def _parse_terms(text: str) -> tuple[list[str], int]:
    terms: list[str] = []
    short = 0
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if len(line) < MIN_TERM:
            short += 1
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        terms.append(line)
    return terms, short


def load_blocklist(root: Path) -> tuple[list[str], bool, int]:
    chunks: list[str] = []
    present = False
    env = os.environ.get("PRIVATE_INFO_BLOCKLIST", "")
    if env.strip():
        chunks.append(env)
        present = True
    local = root / LOCAL_BLOCKLIST
    if local.is_file():
        chunks.append(local.read_text(encoding="utf-8"))
        present = True
    terms: list[str] = []
    short = 0
    seen: set[str] = set()
    for chunk in chunks:
        parsed, count = _parse_terms(chunk)
        short += count
        for term in parsed:
            key = term.casefold()
            if key in seen:
                continue
            seen.add(key)
            terms.append(term)
    return terms, present, short


def load_email_domains(root: Path) -> tuple[str, ...]:
    path = root / "config" / "email-allowlist.txt"
    if not path.is_file():
        return ()
    domains: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().lower()
        if not line or line.startswith("#"):
            continue
        domains.append(line)
    return tuple(domains)


def _connection_findings(path: str, text: str) -> list[str]:
    findings: list[str] = []
    seen: set[int] = set()

    def add(index: int) -> None:
        line = line_number(text, index)
        if line in seen:
            return
        seen.add(line)
        findings.append(
            format_finding(
                RULE,
                path,
                line,
                "database connection string. Remove the credentials or private host and supply the connection at runtime.",
            )
        )

    for match in DB_URL.finditer(text):
        rest = match.group(0).split("://", 1)[1]
        userinfo = None
        hostpart = rest
        if "@" in rest:
            userinfo, hostpart = rest.rsplit("@", 1)
        host = hostpart.split("/")[0].split("?")[0]
        if host.startswith("["):
            hostname = host.split("]")[0].lstrip("[")
        else:
            hostname = host.split(":")[0]
        password = None
        if userinfo and ":" in userinfo:
            password = userinfo.split(":", 1)[1]
        private_host = bool(PRIVATE_IPV4.search(hostname) or PRIVATE_IPV6.search(hostname) or INTERNAL_HOST.search(hostname))
        leaked_password = password is not None and not is_placeholder_secret(password)
        if private_host or leaked_password:
            add(match.start())

    for line_index, line in enumerate(text.splitlines(), 1):
        if line_index in seen:
            continue
        if not ADO_HINT.search(line):
            continue
        password = ADO_PASSWORD.search(line)
        if password and not is_placeholder_secret(password.group(1)):
            seen.add(line_index)
            findings.append(
                format_finding(
                    RULE,
                    path,
                    line_index,
                    "database connection string. Remove the credentials or private host and supply the connection at runtime.",
                )
            )
    return findings


def check_files(files: list[tuple[str, str]], root: Path) -> tuple[list[str], list[str]]:
    terms, present, short = load_blocklist(root)
    domains = load_email_domains(root)
    findings: list[str] = []
    notices: list[str] = []
    if not present:
        notices.append(NO_BLOCKLIST_NOTICE)
    if short:
        notices.append(
            f"private-info: ignored {short} blocklist term(s) shorter than {MIN_TERM} characters. "
            "Use a longer literal so the term does not match unrelated text."
        )

    for path, text in files:
        if path.replace("\\", "/") == "config/email-allowlist.txt":
            continue
        for match in PRIVATE_IPV4.finditer(text):
            findings.append(
                format_finding(
                    RULE,
                    path,
                    line_number(text, match.start()),
                    f"private IP address {match.group(0)!r}. Remove it and supply the address at runtime, not in the repository.",
                )
            )
        for match in PRIVATE_IPV6.finditer(text):
            findings.append(
                format_finding(
                    RULE,
                    path,
                    line_number(text, match.start()),
                    "private IPv6 address. Remove it and supply the address at runtime, not in the repository.",
                )
            )
        for match in INTERNAL_HOST.finditer(text):
            findings.append(
                format_finding(
                    RULE,
                    path,
                    line_number(text, match.start()),
                    f"internal-looking hostname {match.group(0)!r}. Remove it and supply the host at runtime, not in the repository.",
                )
            )
        for match in EMAIL.finditer(text):
            if email_domain_allowed(match.group(0), domains):
                continue
            findings.append(
                format_finding(
                    RULE,
                    path,
                    line_number(text, match.start()),
                    "email address. Remove it, or use an example.com, example.org, example.net, or example.edu "
                    "address. Add other public domains in config/email-allowlist.txt.",
                )
            )
        findings.extend(_connection_findings(path, text))
        lowered = text.casefold()
        reported: set[int] = set()
        for term in terms:
            start = 0
            needle = term.casefold()
            while True:
                at = lowered.find(needle, start)
                if at < 0:
                    break
                line = line_number(text, at)
                if line not in reported:
                    reported.add(line)
                    findings.append(
                        format_finding(
                            RULE,
                            path,
                            line,
                            "matches the project blocklist. Remove the internal term and load it from runtime configuration.",
                        )
                    )
                start = at + len(needle)
    return findings, notices
