## Summary

## Docs

Code changes update all three unless a marker says a doc is not appropriate:

- [ ] `CHANGELOG.md`
- [ ] `kb/`
- [ ] `README.md`

Trivial change: put `[skip-docs]` in the PR body or a commit message, or add the `skip-docs` label. Partial markers: `[skip-changelog]`, `[skip-kb]`, `[skip-readme]`.

## Checks

`sh scripts/py -m lint` passes locally. CI runs the same command and is the gate before Bugbot.
