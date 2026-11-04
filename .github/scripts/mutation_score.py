#!/usr/bin/env python3
"""Summarise a pytest-gremlins JSON report, and write the data for the README badge.

    python3 .github/scripts/mutation_score.py gremlins.json [--badge out.json] [--fail-under 85]

Prints a Markdown summary. `--fail-under` exits 1 below that score, because
pytest-gremlins itself exits 0 however many mutants survive.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CAUGHT = {"zapped", "timeout"}


def badge(score: float) -> dict[str, Any]:
    """The JSON that a Shields.io endpoint badge reads."""
    colour = "brightgreen" if score >= 80 else "yellow" if score >= 60 else "red"
    return {
        "schemaVersion": 1,
        "label": "mutation score",
        "message": f"{score:.0f}%",
        "color": colour,
    }


def summary(report: dict[str, Any]) -> str:
    totals = report["summary"]
    lines = [
        "## Mutation testing",
        "",
        f"**{totals['percentage']:.1f}%** of {totals['total']} mutants caught, "
        f"{totals['survived']} survived, {totals['error']} errors.",
        "",
        "| Script | Caught | Total |",
        "|--------|-------:|------:|",
    ]
    caught: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for result in report["results"]:
        name = Path(result["file_path"]).name
        total[name] += 1
        caught[name] += result["status"] in CAUGHT
    lines += [f"| `{name}` | {caught[name]} | {total[name]} |" for name in sorted(total)]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--badge", type=Path, help="write badge data to this file")
    parser.add_argument("--fail-under", type=float, help="exit 1 below this score")
    args = parser.parse_args(argv[1:])

    report = json.loads(args.report.read_text(encoding="utf-8"))
    score = report["summary"]["percentage"]
    print(summary(report))
    if args.badge:
        args.badge.write_text(json.dumps(badge(score)) + "\n", encoding="utf-8")
    if args.fail_under is not None and score < args.fail_under:
        print(f"\nThe score of {score:.1f}% is below the minimum of {args.fail_under:g}%.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
