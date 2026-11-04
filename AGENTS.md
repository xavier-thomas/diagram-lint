# AGENTS.md

This repository is an agent skill for producing and checking Mermaid and draw.io diagrams.
This file is for working on the skill. `skills/diagram-lint/SKILL.md` is for agents using
it in other projects, so its `diagrams/` paths do not exist here. The equivalent here is
`examples/diagrams/`.

## Layout

| Path | Contents |
|------|----------|
| `skills/diagram-lint/SKILL.md` | The skill's entry point |
| `skills/diagram-lint/references/` | Guides for each toolchain, loaded by `SKILL.md` |
| `skills/diagram-lint/scripts/` | `drawio_lib.py` and the check and preview scripts |
| `skills/diagram-lint/assets/` | Starter files that users copy into their projects |
| `examples/diagrams/` | Worked examples, built with the skill's starter `Makefile` |
| `tests/` | Tests for the scripts. Not installed with the skill |

## Commands

Run these from the repository root after any change to a script:

```bash
ruff check . && mypy --strict skills/diagram-lint/scripts && pytest
```

Check the examples. This needs only Python:

```bash
make -C examples/diagrams check
```

Render the examples. This needs draw.io desktop and mermaid-cli:

```bash
make -C examples/diagrams
```

To find what the tests would miss, run mutation testing. This needs `pytest-gremlins`. CI
reports the score but does not fail on it yet:

```bash
pytest --gremlins --gremlin-parallel
```

Import scripts by name in tests, as in `import drawio_lib`. The tool cannot reach code
loaded from a file path.

CI runs the lint, type, test and example checks on every pull request and push to `master`,
and sends test coverage to SonarQube Cloud. It does not render, so inspecting the render is
still your job.

`lint-before.drawio` fails the layout check on purpose, for the README. It stays out of
`DRAWIO` in the examples' `Makefile`, and `tests/test_examples.py` pins its result.

## Rules

- Use only the Python standard library in `skills/diagram-lint/`. The skill has no install
  step for dependencies.
- Keep the skill self-contained. A release zips `skills/diagram-lint/` alone, so it cannot
  reference files elsewhere in the repository, except by URL. This is why it has its own
  `LICENSE`, which must stay identical to the one at the root.
- Do not rename `skills/diagram-lint/`. The `name` in `SKILL.md` and the release workflow
  both depend on it.
- Never hand-edit `.drawio`, `.svg` or `.png` files. Change the generator or the `.mmd`
  source, then regenerate.
- Add a test for any change to what a script reports, including a case that must still
  pass.
- When behaviour changes, update `README.md`, `SKILL.md` and `references/` to match.
- Keep `check_layout.py` honest: it must report a route it cannot predict as `UNVERIFIED`,
  never as clean.
- Write docs in British English, and wrap prose at about 90 columns.

## Pull requests

- Fill in `.github/PULL_REQUEST_TEMPLATE.md`.
- If a change affects a render, inspect the real `.png` as `SKILL.md` describes and include
  its `Inspected` line. If you could not open the render, say so. A passing check does not
  replace this.

See `CONTRIBUTING.md` for the full process, including releases.
