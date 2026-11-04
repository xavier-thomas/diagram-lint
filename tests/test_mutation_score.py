"""CI score: the summary and badge must report what the pytest-gremlins report says."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

import mutation_score  # noqa: E402


def _report(tmp_path: Path, percentage: float = 75.0) -> Path:
    results = [
        {"file_path": "/x/skills/a.py", "status": "zapped"},
        {"file_path": "/x/skills/a.py", "status": "timeout"},
        {"file_path": "/x/skills/a.py", "status": "survived"},
        {"file_path": "/x/skills/b.py", "status": "zapped"},
    ]
    path = tmp_path / "gremlins.json"
    path.write_text(
        json.dumps(
            {
                "summary": {"total": 4, "survived": 1, "error": 0, "percentage": percentage},
                "results": results,
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("score", "message", "colour"),
    [
        (100, "100%", "brightgreen"),
        (80, "80%", "brightgreen"),
        (79.9, "80%", "yellow"),
        (60, "60%", "yellow"),
        (59.9, "60%", "red"),
    ],
)
def test_badge_rounds_the_score_and_colours_it(score: float, message: str, colour: str) -> None:
    assert mutation_score.badge(score) == {
        "schemaVersion": 1,
        "label": "mutation score",
        "message": message,
        "color": colour,
    }


def test_summary_gives_the_score_and_counts_per_script(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert mutation_score.main(["mutation_score.py", str(_report(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "**75.0%** of 4 mutants caught, 1 survived, 0 errors." in out
    assert "| `a.py` | 2 | 3 |" in out
    assert "| `b.py` | 1 | 1 |" in out


def test_badge_file_is_written_only_when_asked(tmp_path: Path) -> None:
    report = _report(tmp_path)
    target = tmp_path / "badge.json"
    mutation_score.main(["mutation_score.py", str(report)])
    assert not target.exists()
    mutation_score.main(["mutation_score.py", str(report), "--badge", str(target)])
    assert json.loads(target.read_text(encoding="utf-8"))["message"] == "75%"


@pytest.mark.parametrize(
    ("score", "code"),
    [
        pytest.param(85.0, 0, id="at-the-minimum"),
        pytest.param(84.9, 1, id="below-the-minimum"),
    ],
)
def test_fail_under_sets_the_exit_code(score: float, code: int, tmp_path: Path) -> None:
    report = str(_report(tmp_path, percentage=score))
    assert mutation_score.main(["mutation_score.py", report, "--fail-under", "85"]) == code


def test_a_low_score_passes_without_a_minimum(tmp_path: Path) -> None:
    report = str(_report(tmp_path, percentage=1.0))
    assert mutation_score.main(["mutation_score.py", report]) == 0
