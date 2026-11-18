# Checks

`python3 -m lint` runs every check below. The pre-commit hook and the `lint` GitHub Actions workflow run that same command. The suite is meant to finish in seconds. Tests live in `tests/` and `rules/test_*.py`.

```bash
python3 -m lint
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s rules -p 'test_*.py' -v
```

Run one rule with `python3 -m lint <name>`. Names: `secrets`, `private-info`, `banned-clients`, `docs`, `hephaestus`, `custom`.

Failure lines share one shape: `rule: path:line: what is wrong. How to fix it.`

The pre-commit hook is the real guard. It runs before the commit exists, so a coding agent can fix the finding and try again. CI runs after the push. Treat CI as a backstop. Fork pull requests do not receive repository secrets, so a blocklist stored only as a CI secret is not present on those runs. Generic patterns still run.

## secrets

Gitleaks scans the tree with its default rules. `scripts/install-gitleaks.sh` installs the pinned binary and checks its checksum. The runner also accepts `gitleaks` on `PATH` or `GITLEAKS_BIN`.

Paths under `tests/fixtures/` are allowlisted, along with `__pycache__`, `.git`, and `.tools`. Add more path regexes, one per line, in `config/gitleaks-allowlist.txt`. That file is project-owned and is not overwritten by template sync once it exists.

A failure looks like: `secrets: src/app.env:1: possible secret (rule-id). Remove the credential and rotate it if it was real.` The secret value is not printed.

## private-info

Generic patterns always run:

- Private IPv4 addresses in the RFC 1918 ranges (10/8, 172.16/12, 192.168/16) and IPv6 unique-local addresses.
- Hostnames whose last label is `internal`, `corp`, `intranet`, `lan`, `local`, or `localdomain`. A following dot, as in a filename like `settings.local.json`, is not treated as a hostname.
- Email addresses, except the built-in public domains (`example.com`, `example.org`, `example.net`, `example.edu`, `github.com`, `users.noreply.github.com`, `localhost`) and domains listed in `config/email-allowlist.txt`.
- Database connection strings that carry a non-placeholder password or a private host. Placeholder passwords such as `PASSWORD` on an `example.com` host are allowed so docs can show the shape `postgres://USER:PASSWORD@db.example.com:5432/DBNAME`.

The optional project blocklist is never committed. The check reads it from both of these, when they exist:

1. The `PRIVATE_INFO_BLOCKLIST` environment variable. Cursor cloud agents receive this as a Cursor secret. CI maps the GitHub Actions secret of the same name.
2. `config/private-blocklist.txt`, a git-ignored file for humans. `config/private-blocklist.example` shows the shape.

Terms are case-insensitive literals of at least 3 characters. A blocklist hit reports the file and line and does not repeat the term. When neither source is present, the check prints a notice and still runs the generic patterns. That notice is not a failure.

## banned-clients

`config/banned-clients.txt` lists forbidden client libraries and connection-string fragments, one literal per line. The template ships the file with no active lines, so the rule is off until a project fills it in. The file is project-owned. Template sync does not overwrite it once it exists.

A failure names the pattern and points at `config/banned-clients.txt`.

## docs

When the diff against the base branch changes code, the same diff must update:

- `CHANGELOG.md`
- at least one `kb/*.md` page
- `README.md`

Code is a source, script, workflow, or config file. Markdown under `kb/` and the readme itself are not code. See `is_code_path` in `lint/rules/docs_pr.py` for the exact set.

Opt out when a doc update is not appropriate. The marker has to be the first token on its line (a commit subject, or its own line in the pull request body). Mentioning the marker in a sentence does not opt out.

- A line starting with `[skip-docs]`, or a `skip-docs` label, skips all three.
- `[skip-changelog]`, `[skip-kb]`, and `[skip-readme]` skip one each. Several markers can share a line when the line contains only markers. The labels `skip-changelog`, `skip-kb`, and `skip-readme` do the same.

The base ref is `LINT_BASE`, or `origin/$GITHUB_BASE_REF` in Actions, or `origin/main`. The upcoming commit message is `LINT_COMMIT_MSG`. The commit-msg hook sets that from the message you pass to `git commit`. The pre-commit hook runs before the message exists, so a local opt-out needs the variable set as well:

```bash
LINT_COMMIT_MSG='[skip-docs] typo' git commit -m '[skip-docs] typo'
```

CI reads the marker from the commits on the branch and from the pull request body and labels. The marker has to be in one of those for CI to accept the opt-out.

## hephaestus

The check requires `.heph-manifest` from `install.sh --vendor`, a non-empty list of files that are present, and a `# source:` line that names `bveenema/hephaestus`. `install.sh` records the local checkout path. After vendoring, pin the public source:

```bash
scripts/pin-hephaestus-source.sh <commit-sha>
```

That rewrites the source line to `git@github.com:bveenema/hephaestus.git@<commit-sha>`.

## custom

Any `rules/*.py` module other than tests is a project rule. Copy `rules/example_forbidden_token.py`, give the copy a new name, and change the token it forbids. `rules/README.md` describes the `check(files)` contract. Template sync updates the example files and leaves every other file in `rules/` alone.
