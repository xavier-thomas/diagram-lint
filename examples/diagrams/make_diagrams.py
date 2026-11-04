#!/usr/bin/env python3
"""Generate the example topology diagram: one person, one app, one database.

Run from the repository root: python3 examples/diagrams/make_diagrams.py
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE.parent.parent / "skills" / "diagram-lint" / "scripts" / "drawio_lib.py"

spec = importlib.util.spec_from_file_location("drawio_lib", LIB)
assert spec is not None and spec.loader is not None
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


def example() -> None:
    d = lib.Doc("example", width=900, height=640)
    user = d.person(lib.label("Analyst", "Person", "Views the dashboard"), 360, 20, 180, 160)
    app = d.node(
        lib.label("Web app", "Python, Flask", "Serves the dashboard"),
        360, 240, 180, 100, lib.S_CONT,
    )
    db = d.node(
        lib.label("Database", "PostgreSQL", "Stores readings"),
        360, 440, 180, 100, lib.S_DB,
    )
    d.vlink(user, app, "Views")
    d.vlink(app, db, "Reads and writes")
    d.write(str(HERE / "example.drawio"))


if __name__ == "__main__":
    example()
