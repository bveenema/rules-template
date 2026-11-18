# CLAUDE.md

## Development Commands

```bash
# Test
sh scripts/py -m unittest discover -s tests -v && sh scripts/py -m unittest discover -s rules -p 'test_*.py' -v

# Lint
sh scripts/py -m lint

# Build
# This template has no build step.
```

## Hephaestus

Delivery uses the vendored Hephaestus flows from `git@github.com:bveenema/hephaestus.git`: `/orient`, `/autopilot`, `/critique`, `/ship`, and `/finish`.

House rules for agents live in `AGENTS.md` and `.cursor/rules/house-rules.mdc`. Run `sh scripts/py -m lint` before every commit and push, and fix failures yourself.

## Docs requirements

A pull request that changes code updates `CHANGELOG.md`, a page under `kb/`, and `README.md`. Markers for a trivial change are `[skip-docs]`, `[skip-changelog]`, `[skip-kb]`, and `[skip-readme]`.
