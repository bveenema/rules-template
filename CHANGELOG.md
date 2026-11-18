# Changelog

All notable changes to this template are documented here.

## [Unreleased]

### Added

- Vendored Hephaestus from `git@github.com:bveenema/hephaestus.git` via `install.sh --vendor`, with the manifest source pinned to that repository.
- `sh scripts/py -m lint` with secret scanning, private-information checks, banned database clients, docs-on-code-changes, a Hephaestus vendor check, and project rules under `rules/`.
- `sh scripts/py` selects the first Python 3.9+ interpreter among `python3`, `python`, and `py -3`. Hooks, CI, scripts, and docs call that launcher instead of a bare `python3` or `python`.
- Pre-commit hooks (lefthook or `.githooks`) and a GitHub Actions `lint` workflow that run the same command.
- Bugbot guidance in `.cursor/BUGBOT.md` and `.cursor/config/bugbot.yaml`: one review per head, after lint, limited to logic and cross-system bugs.
- Agent rules in `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules/house-rules.mdc`.
- `scripts/sync-from-template.py` to pull template updates into an existing repo without overwriting project-owned config.
- Tests that show each rule failing a bad sample and passing a good one.

### Fixed

- A docs opt-out marker counts only when it is the first token on its line. Mentioning the marker in prose does not skip the check.
