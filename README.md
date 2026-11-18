# rules-template

A public GitHub template for a new repository. It carries a small set of house rules as deterministic checks. The checks run on a pre-commit hook and in GitHub Actions, and they finish in seconds. Coding agents fix those findings before they push. Cursor Bugbot then reviews for judgment calls: logic, business rules, and cross-system bugs.

This repository is public. Do not commit company-specific details: internal hostnames, server names, database names, customer names, company domains, URLs of internal services, or descriptions of internal systems. Anything of that kind comes from configuration supplied at run time.

The checks follow the approach in [Stop burning tokens on code review](https://swizec.com/blog/stop-burning-tokens-on-code-review): run the deterministic rules first, and spend review attention on the rest.

## What you get

- Hephaestus vendored from `git@github.com:bveenema/hephaestus.git` (master) with `install.sh --vendor`. Agents use `/orient`, `/autopilot`, `/critique`, `/ship`, and `/finish`.
- `python3 -m lint` — secrets, private information, banned database clients, docs on every code change, the Hephaestus manifest, and project rules in `rules/`.
- A pre-commit hook and a GitHub Actions workflow named `lint` that run that same command. The workflow is the gate before Bugbot.
- `.cursor/BUGBOT.md` so Bugbot skips what the linters already enforce.
- `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules/house-rules.mdc`.
- `CHANGELOG.md`, `kb/`, and this readme, which code changes keep up to date.
- `scripts/sync-from-template.py` so later copies of the template can update the shared rules without wiping project config.

Details for each rule are in [kb/checks.md](kb/checks.md).

## Create a project

On GitHub, open this repository and choose **Use this template**, then **Create a new repository**. The new repository is a normal repo with this history as its starting point. Clone it over SSH:

```bash
git clone git@github.com:OWNER/NEW-REPO.git
cd NEW-REPO
bash scripts/setup-hooks.sh
bash scripts/install-gitleaks.sh
python3 -m lint
```

Then replace the placeholders:

- Set the project name and description in this readme.
- Add forbidden database clients to `config/banned-clients.txt` if this project has any. An empty file turns that rule off.
- Add gitleaks path regexes to `config/gitleaks-allowlist.txt` if you keep fake secrets under a directory other than `tests/fixtures/`.
- Add public email domains to `config/email-allowlist.txt` if the built-in example and GitHub domains are not enough.
- Create the private blocklist (next section). Do not commit it.
- Add project rules by copying `rules/example_forbidden_token.py`.

`scripts/setup-hooks.sh` uses lefthook when it is installed, and otherwise sets `core.hooksPath` to `.githooks`. Both run `python3 -m lint`.

## Configure the private-information blocklist

Generic patterns (private addresses, internal-looking hostnames, connection strings, email addresses) are built in and always run. A project blocklist adds literals that only that project cares about. The blocklist is never committed. The check reads it from whichever of these exist:

| Source | Who uses it |
| --- | --- |
| Environment variable `PRIVATE_INFO_BLOCKLIST` | Cursor cloud agents, via a Cursor secret. CI, via a GitHub Actions secret of the same name. |
| `config/private-blocklist.txt` | People working in a checkout. The file is git-ignored. Copy `config/private-blocklist.example`. |

One term per line, case-insensitive, at least 3 characters. `#` starts a comment. If both sources exist, the terms are combined. If neither exists, the check prints a notice and still runs the generic patterns. The notice is not a failure.

The pre-commit hook is the real guard: it runs on the machine that has the blocklist, before the commit. CI is a backstop. It runs after the push, and fork pull requests do not receive secrets, so they only get the generic patterns.

The workflow passes the secret through:

```yaml
env:
  PRIVATE_INFO_BLOCKLIST: ${{ secrets.PRIVATE_INFO_BLOCKLIST }}
```

## Run the checks

```bash
python3 -m lint
python3 -m lint secrets          # one rule
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s rules -p 'test_*.py' -v
```

Python 3.11 or newer is enough. The only extra binary is gitleaks, installed with `scripts/install-gitleaks.sh`.

A code change has to update `CHANGELOG.md`, a page under `kb/`, and `README.md`. For a trivial change, put `[skip-docs]` in the commit message or the pull request body, or add the `skip-docs` label. Partial markers are `[skip-changelog]`, `[skip-kb]`, and `[skip-readme]`. The pre-commit hook runs before git has the message, so export the same text when you opt out locally:

```bash
LINT_COMMIT_MSG='[skip-docs] typo' git commit -m '[skip-docs] typo'
```

## Review order

1. **Lint.** The hook runs `python3 -m lint` before the commit. GitHub Actions runs it again on the pull request. Require the `lint` check in branch protection.
2. **Bugbot, once per head.** `.cursor/config/bugbot.yaml` sets `triggers.frequency: everyPush`. Bugbot reads that file from the base branch, so it takes effect after it is merged. `.cursor/BUGBOT.md` tells Bugbot to look for logic, business-rule, and cross-system bugs, and to skip findings the linters already report.
3. **Human review** after lint is green and Bugbot has commented.

## Hephaestus

The vendored adapters and `.heph-manifest` came from `install.sh --vendor` on master of `git@github.com:bveenema/hephaestus.git`. The manifest `# source:` line is pinned to that repository. `install.sh` writes a local checkout path; `scripts/pin-hephaestus-source.sh <commit>` rewrites it. The `hephaestus` lint rule fails if the manifest is missing, incomplete, or pointed somewhere else.

To refresh later, run that repository's `update.sh --vendor` against this checkout, then pin the new commit and commit the result.

## Add a project rule

Copy `rules/example_forbidden_token.py` to a new name under `rules/`, change the token it forbids, and add a `test_*.py` next to it. `rules/README.md` is the contract. `python3 -m lint` loads every non-test module in that folder.

## Adopt an existing repo

The sync script copies template-owned rules and docs into a repo that is already in progress. It does not overwrite project-owned files: `config/banned-clients.txt`, the allowlists, `config/private-blocklist.txt`, `README.md`, `CHANGELOG.md`, `kb/index.md`, `CLAUDE.md`, `.gitignore`, or any project rule other than the example.

```bash
git clone git@github.com:bveenema/rules-template.git /tmp/rules-template
python3 /tmp/rules-template/scripts/sync-from-template.py --source /tmp/rules-template --dest .
```

`--dry-run` prints the copies and the files it will keep. The script clones over SSH and does not fall back to HTTPS. Pass `--source` with a local checkout when you already have one.

Sync does not vendor Hephaestus. If the destination has no `.heph-manifest`, vendor it from `git@github.com:bveenema/hephaestus.git` and pin the source. Then run `scripts/setup-hooks.sh`, `scripts/install-gitleaks.sh`, and `python3 -m lint`.

Later updates from a checkout that already has the script:

```bash
python3 scripts/sync-from-template.py
```

`kb/checks.md` is replaced on sync. Keep project notes on other pages under `kb/`.

## License of vendored Hephaestus

The Hephaestus adapters are MIT. See [LICENSES/hephaestus.txt](LICENSES/hephaestus.txt).
