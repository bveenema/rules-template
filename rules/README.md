# Project rules

`python3 -m lint` loads every `rules/*.py` module and calls `check(files)`.

- `files` is a list of `(relative path, text)` for text files in the git index.
- Return a list of failure strings. An empty list means the rule passed.
- Start each string with the rule name, then the path and line, then what is wrong and how to fix it.
- Name tests `test_*.py` or `*_test.py`. Those files are not loaded as rules.
- `example_forbidden_token.py` is the template's example. Copy it and change `TOKEN`. The template sync updates the example file in place, so keep project rules in other filenames.

Run the example test:

```bash
python3 -m unittest discover -s rules -p 'test_*.py' -v
```
