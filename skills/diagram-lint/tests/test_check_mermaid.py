"""Self-messages: check_mermaid fails on visible text, whatever the arrow or actor."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_mermaid


def _faults(tmp_path: Path, source: str) -> list[str]:
    path = tmp_path / "d.mmd"
    path.write_text(source, encoding="utf-8")
    return check_mermaid.check(path)


@pytest.mark.parametrize(
    "line",
    [
        "A->>A: text",
        "A-->>A: text",
        "A->A: text",
        "A-->A: text",
        "A-xA: text",
        "A--)A: text",
        "A<<->>A: text",
        "A->>+A: activates",
        "A-->>-A: deactivates",
        "web-app->>web-app: hyphen in the id",
        "A ->> A : spaced",
    ],
)
def test_visible_text_fails(tmp_path: Path, line: str) -> None:
    assert len(_faults(tmp_path, f"sequenceDiagram\n    {line}\n")) == 1


@pytest.mark.parametrize(
    "line",
    [
        "A->>A: #nbsp;",
        "A->>A:",
        "A->>B: to another actor",
        "web-app->>web-api: shared prefix",
        "%% A->>A: commented out",
        "Note right of A: A->>A: inside a note",
    ],
)
def test_allowed_lines_pass(tmp_path: Path, line: str) -> None:
    assert _faults(tmp_path, f"sequenceDiagram\n    {line}\n") == []


def test_fault_names_the_line(tmp_path: Path) -> None:
    faults = _faults(tmp_path, "sequenceDiagram\n    A->>B: hi\n    A->>A: parse\n")
    assert ":3:" in faults[0]
    assert "'parse'" in faults[0]


@pytest.mark.parametrize(
    "header",
    [
        "%%{init: {}}%%\nsequenceDiagram",
        "---\ntitle: Title\n---\nsequenceDiagram",
    ],
)
def test_sequence_diagram_found_below_a_header(tmp_path: Path, header: str) -> None:
    assert len(_faults(tmp_path, f"{header}\n    A->>A: text\n")) == 1


def test_other_diagram_types_are_skipped(tmp_path: Path) -> None:
    assert _faults(tmp_path, "stateDiagram-v2\n    s1 --> s1: retry\n") == []


def test_exit_codes(tmp_path: Path) -> None:
    clean = tmp_path / "clean.mmd"
    clean.write_text("sequenceDiagram\n    A->>B: hi\n", encoding="utf-8")
    bad = tmp_path / "bad.mmd"
    bad.write_text("sequenceDiagram\n    A->>A: hi\n", encoding="utf-8")
    assert check_mermaid.main(["check_mermaid.py"]) == 0
    assert check_mermaid.main(["check_mermaid.py", str(clean)]) == 0
    assert check_mermaid.main(["check_mermaid.py", str(clean), str(bad)]) == 1
