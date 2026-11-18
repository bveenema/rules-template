#!/usr/bin/env bash
# Install the pinned gitleaks release and verify its checksum.
# Usage: scripts/install-gitleaks.sh [destination-binary]
set -euo pipefail

VERSION="8.30.1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$ROOT/.tools/gitleaks}"
CHECKSUMS="$ROOT/scripts/gitleaks-v8.30.1-checksums.txt"

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) arch="x64" ;;
  aarch64|arm64) arch="arm64" ;;
  *) echo "secrets: unsupported architecture $arch. Install gitleaks ${VERSION} yourself and put it on PATH." >&2; exit 1 ;;
esac
case "$os" in
  linux|darwin) ;;
  *) echo "secrets: unsupported OS $os. Install gitleaks ${VERSION} yourself and put it on PATH." >&2; exit 1 ;;
esac

name="gitleaks_${VERSION}_${os}_${arch}.tar.gz"
sum="$(awk -v name="$name" '$2 == name { print $1 }' "$CHECKSUMS")"
if [ -z "$sum" ]; then
  echo "secrets: no checksum for $name in scripts/gitleaks-v8.30.1-checksums.txt." >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
archive="$tmp/$name"
curl -fsSL -o "$archive" "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/${name}"
echo "${sum}  ${archive}" | sha256sum -c -
tar -xzf "$archive" -C "$tmp" gitleaks
mkdir -p "$(dirname "$DEST")"
install -m 0755 "$tmp/gitleaks" "$DEST"
echo "Installed gitleaks ${VERSION} at ${DEST}"
