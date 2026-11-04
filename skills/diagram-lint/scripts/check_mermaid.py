#!/usr/bin/env python3
"""Fail on a Mermaid sequence diagram whose self-message carries visible text.

    python3 scripts/check_mermaid.py diagrams/*.mmd

Mermaid centres a self-message's label on the lifeline, and `autonumber` puts the
step's number on the same line. The text belongs in a note instead:

    A->>A: #nbsp;
    Note right of A: what the step does

Exits 0 if clean, or 1 and prints every self-message to move.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
import re
import sys
from pathlib import Path

SELF_MESSAGE = re.compile(r"^\s*(.+?)\s*(?:<<)?--?(?:>>?|x|\))[+-]?\s*\1\s*:\s*(.*?)\s*$")
HIDDEN_LABELS = {"", "#nbsp;"}


def check(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    # State and class diagrams use the same syntax for a labelled loop, and it is fine there.
    if not any(line.strip().startswith("sequenceDiagram") for line in lines):
        return []
    faults = []
    for number, line in enumerate(lines, start=1):
        match = SELF_MESSAGE.match(line)
        if match and match[2] not in HIDDEN_LABELS:
            faults.append(f"{path}:{number}: move {match[2]!r} from the self-message to a note")
    return faults


def main(argv: list[str]) -> int:
    faults = [fault for name in argv[1:] for fault in check(Path(name))]
    for fault in faults:
        print(fault)
    print(f"{len(argv) - 1} files, {len(faults)} self-message labels to move")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
