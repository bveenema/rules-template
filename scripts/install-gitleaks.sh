#!/usr/bin/env bash
# Install the pinned gitleaks release and verify its checksum.
# Usage: scripts/install-gitleaks.sh [destination-binary]
#        scripts/install-gitleaks.sh --print-asset
#
# Linux and macOS download a tar.gz. Git Bash for Windows (uname reports
# MINGW, MSYS, or Cygwin) downloads the matching windows x64 or arm64 zip
# and installs gitleaks.exe. The zip is extracted with unzip, or with
# `sh scripts/py -m zipfile -e` when unzip is not installed.
set -euo pipefail

VERSION="8.30.1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECKSUMS="$ROOT/scripts/gitleaks-v8.30.1-checksums.txt"

# Print the release asset file name for this machine.
asset_name() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) arch="x64" ;;
    aarch64|arm64) arch="arm64" ;;
    *)
      echo "secrets: unsupported architecture $arch. Install gitleaks ${VERSION} yourself and put it on PATH." >&2
      return 1
      ;;
  esac
  case "$os" in
    linux)
      printf 'gitleaks_%s_linux_%s.tar.gz\n' "$VERSION" "$arch"
      ;;
    darwin)
      printf 'gitleaks_%s_darwin_%s.tar.gz\n' "$VERSION" "$arch"
      ;;
    mingw*|msys*|cygwin*)
      printf 'gitleaks_%s_windows_%s.zip\n' "$VERSION" "$arch"
      ;;
    *)
      echo "secrets: unsupported OS $os. On Windows, run this from Git Bash (MINGW, MSYS, or Cygwin). Otherwise install gitleaks ${VERSION} yourself and put it on PATH." >&2
      return 1
      ;;
  esac
}

if [ "${1:-}" = "--print-asset" ]; then
  asset_name
  exit
fi

name="$(asset_name)"
case "$name" in
  *.zip) binary_name="gitleaks.exe" ;;
  *) binary_name="gitleaks" ;;
esac
DEST="${1:-$ROOT/.tools/$binary_name}"

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

if [ "$binary_name" = "gitleaks.exe" ]; then
  if command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$archive" -d "$tmp"
  else
    sh "$ROOT/scripts/py" -m zipfile -e "$archive" "$tmp"
  fi
else
  tar -xzf "$archive" -C "$tmp" "$binary_name"
fi

if [ ! -f "$tmp/$binary_name" ]; then
  echo "secrets: $name did not contain $binary_name." >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
install -m 0755 "$tmp/$binary_name" "$DEST"
echo "Installed gitleaks ${VERSION} at ${DEST}"
