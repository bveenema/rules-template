<!-- rules-template:house-rules:start -->
## House rules

These rules apply to every coding agent in a repository created from this template.

- Use the Hephaestus flows for delivery work: `/orient`, `/autopilot`, `/critique`, `/ship`, and `/finish`. The command files are vendored in this repo from `git@github.com:bveenema/hephaestus.git`.
- Before every commit and before every push, run `python3 -m lint`. If it reports a failure, fix it yourself and run the command again. Do not push code that fails lint.
- When a change touches code, update `CHANGELOG.md`, a page under `kb/`, and `README.md` in the same pull request. Use `[skip-docs]` only when a docs update is not appropriate for a trivial change. Partial markers are `[skip-changelog]`, `[skip-kb]`, and `[skip-readme]`.
- Never print secrets, credentials, connection strings, or project blocklist terms. The private-info check reports the file and line for a blocklist match and does not repeat the term.
- Do not commit company-specific or environment-specific values. Private addresses, internal hostnames, and customer terms belong in runtime configuration: the `PRIVATE_INFO_BLOCKLIST` environment variable or the git-ignored file `config/private-blocklist.txt`.
<!-- rules-template:house-rules:end -->
