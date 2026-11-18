#!/usr/bin/env bash
# Point this clone at the shared lint hooks.
# Uses lefthook when it is installed, and .githooks otherwise.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"
chmod +x .githooks/pre-commit .githooks/commit-msg scripts/install-gitleaks.sh scripts/pin-hephaestus-source.sh scripts/sync-from-template.py

if command -v lefthook >/dev/null 2>&1; then
  lefthook install
  echo "Installed lefthook hooks from lefthook.yml."
else
  git config core.hooksPath .githooks
  echo "lefthook is not installed. Using .githooks via core.hooksPath."
  echo "Install lefthook and run this script again to switch."
fi
echo "Run python3 -m lint before you commit. The hook runs the same command."
