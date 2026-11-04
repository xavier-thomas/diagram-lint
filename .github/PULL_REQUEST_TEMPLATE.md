## Summary

<!-- What changed and why. Link any related issue. -->

## Checks

- [ ] `ruff check . && mypy --strict skills/diagram-lint/scripts && pytest` passes
- [ ] `make -C examples/diagrams check` passes
- [ ] Any change to what a script reports has a test
- [ ] `README.md`, `SKILL.md` and `references/` still match the behaviour

## Render inspection

<!--
If this changes a diagram, or anything that affects how one renders, follow "Inspect the
render" in skills/diagram-lint/SKILL.md and replace this comment with:

Inspected <file>.png at <date>: <failures fixed, or "none">

If you could not open the render, say so instead. Otherwise, delete this section.
-->
