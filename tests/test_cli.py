"""Command lines: each script run as a program must exit as `make check` and CI rely on."""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load_lib() -> Any:
    spec = importlib.util.spec_from_file_location("drawio_lib", SCRIPTS / "drawio_lib.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lib = _load_lib()


def _exit_code(monkeypatch: pytest.MonkeyPatch, script: str, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", [script, *args])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SCRIPTS / script), run_name="__main__")
    assert isinstance(caught.value.code, int)
    return caught.value.code


def _drawio(tmp_path: Path, name: str, *, pinned: bool) -> str:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 200, 100, 50, lib.S_CONT)
    if pinned:
        doc.vlink(a, b, "uses")
    else:
        doc.edge(a, b, "uses")
    path = tmp_path / name
    doc.write(str(path))
    return str(path)


def _mmd(tmp_path: Path, name: str, line: str) -> str:
    path = tmp_path / name
    path.write_text(f"sequenceDiagram\n    {line}\n", encoding="utf-8")
    return str(path)


def test_check_layout_exit_codes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    good = _drawio(tmp_path, "good.drawio", pinned=True)
    unverified = _drawio(tmp_path, "unverified.drawio", pinned=False)
    assert _exit_code(monkeypatch, "check_layout.py", good) == 0
    assert _exit_code(monkeypatch, "check_layout.py", unverified) == 1
    assert _exit_code(monkeypatch, "check_layout.py") == 2


def test_check_mermaid_exit_codes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    good = _mmd(tmp_path, "good.mmd", "A->>B: text")
    bad = _mmd(tmp_path, "bad.mmd", "A->>A: text")
    assert _exit_code(monkeypatch, "check_mermaid.py", good) == 0
    assert _exit_code(monkeypatch, "check_mermaid.py", bad) == 1


def test_content_diff_exit_codes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    one = _drawio(tmp_path, "one.drawio", pinned=True)
    two = _drawio(tmp_path, "two.drawio", pinned=False)
    other = tmp_path / "other.drawio"
    other.write_text(Path(one).read_text(encoding="utf-8").replace("uses", "calls"), "utf-8")
    assert _exit_code(monkeypatch, "content_diff.py", one, two) == 0
    assert _exit_code(monkeypatch, "content_diff.py", one, str(other)) == 1
    assert _exit_code(monkeypatch, "content_diff.py", one) == 2


def test_preview_renders_every_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    one = _drawio(tmp_path, "one.drawio", pinned=True)
    two = _drawio(tmp_path, "two.drawio", pinned=True)
    monkeypatch.setattr(sys, "argv", ["preview.py", one, two])
    runpy.run_path(str(SCRIPTS / "preview.py"), run_name="__main__")
    assert (tmp_path / "one.preview.svg").exists()
    assert (tmp_path / "two.preview.svg").exists()


def test_preview_without_files_prints_usage(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _exit_code(monkeypatch, "preview.py") == 2
    assert "usage" in capsys.readouterr().err
