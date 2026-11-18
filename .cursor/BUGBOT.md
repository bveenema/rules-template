# Bugbot review rules

Review order for this repository:

1. The `lint` GitHub Actions check runs first and must pass. It enforces the deterministic rules in `kb/checks.md`.
2. Bugbot reviews once per new pull request head.
3. Human review comes after lint and Bugbot.

`.cursor/config/bugbot.yaml` sets `triggers.frequency: everyPush`, which is one review each time the head changes. Bugbot reads that file from the pull request's base branch.

## Look for

- Logic bugs, broken invariants, and incorrect control flow
- Business-rule mistakes
- Cross-system bugs: mismatched contracts between code, scripts, CI, and docs

## Do not flag

- Speculative edge cases that the diff does not exercise
- Invented security concerns
- Pull-request description fluff, tone, or changelog wording
- Anything the deterministic linters already enforce:
  - secrets (gitleaks)
  - private information (private IP addresses, internal-looking hostnames, connection strings, email addresses, the project blocklist)
  - banned database clients (`config/banned-clients.txt`)
  - docs on every code change (`CHANGELOG.md`, `kb/`, `README.md`)
  - the Hephaestus vendor manifest source
  - custom rules in `rules/`

Leave those to `python3 -m lint`. If lint failed, do not repeat its findings.
