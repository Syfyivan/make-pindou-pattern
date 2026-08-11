#!/usr/bin/env python3
"""Build a directory-style Skill ZIP for the ByteDance AgentBuddy platform."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "make-pindou-pattern"
SKILL_FILES = ("SKILL.md", "agents", "references", "scripts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="1.0.0", help="Semantic version for the plugin bundle")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist")
    return parser.parse_args()


def add_path(archive: zipfile.ZipFile, source: Path, destination: Path) -> None:
    if source.is_dir():
        for child in sorted(source.rglob("*")):
            if (
                child.is_file()
                and "__pycache__" not in child.parts
                and child.suffix != ".pyc"
                and child.name != Path(__file__).name
            ):
                relative = child.relative_to(source)
                add_path(archive, child, destination / relative)
        return

    info = zipfile.ZipInfo.from_file(source, destination.as_posix())
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, source.read_bytes())


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{SKILL_NAME}-skill-{args.version}.zip"
    skill_root = Path("skills") / SKILL_NAME

    with zipfile.ZipFile(output, "w") as archive:
        for name in SKILL_FILES:
            add_path(archive, REPO_ROOT / name, skill_root / name)
        add_path(archive, REPO_ROOT / "LICENSE", skill_root / "LICENSE")

    print(output.resolve())


if __name__ == "__main__":
    main()
