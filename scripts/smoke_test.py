#!/usr/bin/env python3
"""Repeatable smoke test for the deterministic converter."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPT_DIR = Path(__file__).resolve().parent


def make_fixture(path: Path) -> None:
    image = Image.new("RGB", (512, 512), "#00ff00")
    draw = ImageDraw.Draw(image)
    skin = "#ffc4aa"
    dark = "#1d1414"
    rose = "#cd9391"
    beige = "#f2d9ba"
    white = "#fffdf0"
    # Four overlapping head/shoulder masses form one deliberately sturdy cluster.
    draw.ellipse((150, 20, 362, 232), fill=dark)
    draw.ellipse((35, 170, 247, 382), fill=rose)
    draw.ellipse((265, 170, 477, 382), fill=white)
    draw.ellipse((150, 280, 362, 492), fill=beige)
    for box in ((194, 70, 318, 202), (79, 208, 203, 340), (309, 208, 433, 340), (194, 318, 318, 450)):
        draw.ellipse(box, fill=skin, outline=dark, width=10)
        left, top, right, bottom = box
        draw.ellipse((left + 31, top + 50, left + 48, top + 75), fill=dark)
        draw.ellipse((right - 48, top + 50, right - 31, top + 75), fill=dark)
        draw.arc((left + 42, top + 75, right - 42, bottom - 25), 20, 160, fill=dark, width=7)
    image.save(path)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pindou-skill-") as temp:
        root = Path(temp)
        fixture = root / "fixture.png"
        output = root / "out"
        make_fixture(fixture)
        completed = subprocess.run(
            [str(SCRIPT_DIR / "pindou"), str(fixture), "--output-dir", str(output), "--grid", "72", "--colors", "18", "--max-beads", "3400", "--strict"],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        assert report["components"] == 1, report
        assert report["safe_for_pendant"] is True, report
        assert report["within_bead_budget"] is True, report
        assert report["passes_quality_gate"] is True, report
        assert {path.name for path in output.iterdir()} == {"chart.png", "chart.pdf"}
    print("make-pindou-pattern smoke test passed")


if __name__ == "__main__":
    main()
