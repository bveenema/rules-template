#!/usr/bin/env bash
# Point .heph-manifest at bveenema/hephaestus.
# install.sh records the local checkout path in the "# source:" line. Replace
# that with the upstream SSH URL and the commit you vendored.
#
# Usage: scripts/pin-hephaestus-source.sh <commit-sha>
set -euo pipefail

sha="${1:-}"
if ! [[ "$sha" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
  echo "usage: scripts/pin-hephaestus-source.sh <commit-sha>" >&2
  exit 2
fi

root="$(git rev-parse --show-toplevel)"
manifest="$root/.heph-manifest"
if [[ ! -f "$manifest" ]]; then
  echo "hephaestus: .heph-manifest is missing. Run install.sh --vendor from a checkout of git@github.com:bveenema/hephaestus.git first." >&2
  exit 1
fi

tmp="$(mktemp)"
if ! awk -v sha="$sha" '
  BEGIN { found = 0 }
  /^# source:/ {
    print "# source: git@github.com:bveenema/hephaestus.git@" sha
    found = 1
    next
  }
  { print }
  END { if (!found) exit 3 }
' "$manifest" > "$tmp"; then
  rm -f "$tmp"
  echo "hephaestus: .heph-manifest has no # source: line. Re-run install.sh --vendor from git@github.com:bveenema/hephaestus.git." >&2
  exit 1
fi
mv "$tmp" "$manifest"
echo "Pinned .heph-manifest source to git@github.com:bveenema/hephaestus.git@${sha}"
