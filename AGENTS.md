# AGENTS.md

<!-- Index of agents available in this project. Customize the Local section;
     the Shared section lists what hephaestus provides. -->

## Development Commands
See CLAUDE.md "Development Commands" — agents read test/lint/build commands from there.

## Local Agents
<!-- Project-specific agents in .claude/agents/ that this project owns. -->
| Agent | Role |
|---|---|
| _(none yet)_ | |

## Shared Agents (hephaestus)
| Agent | Role | Access |
|---|---|---|
| **coder** | Implements a focused task; parallel coders for independent changes | Edit + shell, isolated worktree |
| **reviewer** | Adversarial code review — evidence-cited findings, 0–100 score | Read + shell (instructed read-only) |
| **tester** | Runs quality gates, returns structured pass/fail | Read + shell (instructed read-only) |
| **explorer** | Investigates the codebase, reports findings | Read + shell (instructed read-only) |
| **researcher** | Web research with source cross-referencing | Web + read, no shell |

## Conventions
- Agents return structured output (status, files, verdicts) — never raw logs.
- Only the coder modifies files; review and implementation stay separated.
- Retry limits and wind-down rules are carried by the commands themselves. Add a `## Workflow Rules` section to CLAUDE.md only to override them.

<!-- rules-template:house-rules:start -->
## House rules

These rules apply to every coding agent in a repository created from this template.

- Use the Hephaestus flows for delivery work: `/orient`, `/autopilot`, `/critique`, `/ship`, and `/finish`. The command files are vendored in this repo from `git@github.com:bveenema/hephaestus.git`.
- Before every commit and before every push, run `python3 -m lint`. If it reports a failure, fix it yourself and run the command again. Do not push code that fails lint.
- When a change touches code, update `CHANGELOG.md`, a page under `kb/`, and `README.md` in the same pull request. Use `[skip-docs]` only when a docs update is not appropriate for a trivial change. Partial markers are `[skip-changelog]`, `[skip-kb]`, and `[skip-readme]`.
- Never print secrets, credentials, connection strings, or project blocklist terms. The private-info check reports the file and line for a blocklist match and does not repeat the term.
- Do not commit company-specific or environment-specific values. Private addresses, internal hostnames, and customer terms belong in runtime configuration: the `PRIVATE_INFO_BLOCKLIST` environment variable or the git-ignored file `config/private-blocklist.txt`.
<!-- rules-template:house-rules:end -->
