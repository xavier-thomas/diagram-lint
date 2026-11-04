#!/usr/bin/env python3
"""Generate this project's draw.io diagrams, one function each."""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
# This skill's directory. Keep it in step with SKILL in the Makefile.
SKILL = HERE.parent / ".claude" / "skills" / "diagram-lint"

spec = importlib.util.spec_from_file_location("drawio_lib", SKILL / "scripts" / "drawio_lib.py")
assert spec is not None and spec.loader is not None
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


def example() -> None:
    d = lib.Doc("example", width=600, height=400)
    app = d.node(lib.label("App", "Python"), 200, 40, 180, 100, lib.S_CONT)
    db = d.node(lib.label("Database", "PostgreSQL"), 200, 240, 180, 100, lib.S_DB)
    d.vlink(app, db, "Reads and writes")
    d.write(str(HERE / "example.drawio"))


if __name__ == "__main__":
    example()
