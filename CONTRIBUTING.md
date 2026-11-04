# Contributing

Bug reports and pull requests are welcome. For a layout check that gets something wrong,
include the `.drawio` or `.mmd` file, or the smallest one that shows the problem, along
with the script's output.

## Setup

You need Python 3.12 or later, and the development tools:

```bash
pip install ruff mypy pytest
```

To render diagrams, you also need
[draw.io desktop](https://github.com/jgraph/drawio-desktop/releases) and
[mermaid-cli](https://github.com/mermaid-js/mermaid-cli). The checks and tests do not
need them.

## Run the checks

[CI](.github/workflows/ci.yml) runs these on every pull request to `master`. Run them
locally first:

```bash
ruff check . && mypy --strict skills/diagram-lint/scripts && pytest
```

```bash
make -C examples/diagrams check
```

## Make a change

- **Keep the skill self-contained.** Everything in `skills/diagram-lint/` ships to users,
  and nothing outside it does. Scripts must use only the Python standard library.
- **Test what the scripts report.** Add a test in `tests/` for any new or changed check,
  including the case that must still pass.
- **Keep the docs in step.** A change in behaviour may also affect `README.md`, `SKILL.md`
  and the guides in `references/`.
- **Do not hand-edit generated files.** The `.drawio`, `.svg` and `.png` files are
  generated. To change the example, edit `make_diagrams.py` or the `.mmd` file, then run
  `make -C examples/diagrams`.
- **Only commit renders that changed for a reason.** PNG bytes drift with fonts and browser
  versions, so leave out any re-render that has no design change.

## Open a pull request

Fill in the [template](.github/PULL_REQUEST_TEMPLATE.md). If the change affects a render,
follow "Inspect the render" in [`SKILL.md`](skills/diagram-lint/SKILL.md) and add its
`Inspected` line.

## Release

Update the version in `pyproject.toml` and `SKILL.md`, then push a `v*` tag from `master`.
The [release workflow](.github/workflows/release.yml) zips the skill and publishes it as a
GitHub release.

## Licence

By contributing, you agree that your work is licensed under
[Apache 2.0](LICENSE).
