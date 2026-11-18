"""Confirm Hephaestus is vendored and the manifest names bveenema/hephaestus."""

from __future__ import annotations

from pathlib import Path

from lint.finding import format_finding

RULE = "hephaestus"
MANIFEST = ".heph-manifest"
SOURCE_SLUG = "bveenema/hephaestus"
# Reject the other public fork if a manifest was generated from it.
FORBIDDEN_SLUG = "amur" + "shak/hephaestus"
FIX = (
    "Vendor Hephaestus by running install.sh --vendor from a checkout of "
    "git@github.com:bveenema/hephaestus.git (master), then run "
    "scripts/pin-hephaestus-source.sh <commit> so the manifest # source: line "
    "names that repository. Do not point the manifest at a different fork."
)


def check(root: Path) -> list[str]:
    path = root / MANIFEST
    if not path.is_file():
        return [format_finding(RULE, MANIFEST, None, f"manifest is missing. {FIX}")]
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[str] = []
    if not any(line.startswith("# hephaestus vendor") for line in lines):
        findings.append(
            format_finding(
                RULE,
                MANIFEST,
                None,
                "manifest is not a Hephaestus vendor install. " + FIX,
            )
        )
    source_lines = [line for line in lines if line.startswith("# source:")]
    if not source_lines:
        findings.append(format_finding(RULE, MANIFEST, None, "manifest has no # source: line. " + FIX))
    else:
        source = source_lines[0]
        if SOURCE_SLUG not in source or FORBIDDEN_SLUG in source:
            findings.append(
                format_finding(
                    RULE,
                    MANIFEST,
                    None,
                    "manifest source does not point at bveenema/hephaestus. " + FIX,
                )
            )
    listed = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    if not listed:
        findings.append(
            format_finding(RULE, MANIFEST, None, "manifest lists no vendored files. " + FIX)
        )
    for rel in listed:
        if not (root / rel).exists():
            findings.append(
                format_finding(
                    RULE,
                    rel,
                    None,
                    "listed in .heph-manifest but missing from the tree. " + FIX,
                )
            )
    return findings
