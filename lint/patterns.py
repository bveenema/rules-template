"""Generic private-information patterns.

The expressions are assembled from pieces so this module's source does not
contain a literal private address, internal hostname, or email address.
"""

import re

_OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"

_HOST_SUFFIXES = ("internal", "corp", "intranet", "lan", "local", "localdomain")

ALLOW_EMAIL_DOMAINS = (
    "example.com",
    "example.org",
    "example.net",
    "example.edu",
    "github.com",
    "users.noreply.github.com",
    "localhost",
)

PASSWORD_PLACEHOLDERS = {
    "password",
    "pass",
    "secret",
    "changeme",
    "example",
    "placeholder",
    "redacted",
    "user",
    "username",
    "todo",
    "xxx",
}

_DB_SCHEMES = (
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "mongodb+srv",
    "redis",
    "rediss",
    "amqp",
    "amqps",
    "mssql",
    "sqlserver",
)


def _ipv4() -> re.Pattern[str]:
    ten = r"10\." + _OCTET + r"\." + _OCTET + r"\." + _OCTET
    # The 172/12 range is written as a second-octet class so this file stays generic.
    block = r"172\.(?:1[6-9]|2\d|3[0-1])\." + _OCTET + r"\." + _OCTET
    lan = r"192\.168\." + _OCTET + r"\." + _OCTET
    return re.compile(rf"(?<!\d)(?:{ten}|{block}|{lan})(?!\d)")


def _ipv6_ula() -> re.Pattern[str]:
    # IPv6 unique-local addresses.
    return re.compile(r"(?i)(?<![0-9a-f:])(?:fc[0-9a-f]{2}|fd[0-9a-f]{2}):[0-9a-f]{0,4}:")


def _internal_host() -> re.Pattern[str]:
    label = r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?"
    suffixes = "|".join(_HOST_SUFFIXES)
    # A following dot means the token continues (for example a filename
    # such as settings.local.json), so it is not a hostname.
    return re.compile(rf"(?i)(?<![a-z0-9.-])(?:{label}\.)+(?:{suffixes})(?![a-z0-9.-])")


def _db_url() -> re.Pattern[str]:
    schemes = "|".join(re.escape(scheme) for scheme in _DB_SCHEMES)
    return re.compile(rf"(?i)\b(?:{schemes})://[^\s<>\"'`]+")


PRIVATE_IPV4 = _ipv4()
PRIVATE_IPV6 = _ipv6_ula()
INTERNAL_HOST = _internal_host()
EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
DB_URL = _db_url()
ADO_HINT = re.compile(r"(?i)\b(?:server|data\s+source|database|initial\s+catalog)\s*=")
ADO_PASSWORD = re.compile(r"(?i)\b(?:password|pwd)\s*=\s*([^\s;]+)")


def is_placeholder_secret(value: str) -> bool:
    cleaned = value.strip().strip("\"'").lower()
    if cleaned in PASSWORD_PLACEHOLDERS:
        return True
    if cleaned.startswith("${") or cleaned.startswith("<") or cleaned.startswith("%"):
        return True
    if cleaned and (set(cleaned) <= {"*"} or set(cleaned) <= {"x"}):
        return True
    return False


def email_domain_allowed(address: str, extra_domains: tuple[str, ...] = ()) -> bool:
    domain = address.rsplit("@", 1)[-1].lower().rstrip(".")
    allowed = tuple(part.lower() for part in (*ALLOW_EMAIL_DOMAINS, *extra_domains))
    return any(domain == item or domain.endswith("." + item) for item in allowed)


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1
