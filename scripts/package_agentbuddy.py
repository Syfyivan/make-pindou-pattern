#!/usr/bin/env python3
"""Build an AgentBuddy-compatible plugin ZIP for the ByteDance Skill platform."""

from __future__ import annotations

import argparse
import json
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


def manifest(version: str) -> dict[str, object]:
    return {
        "name": SKILL_NAME,
        "version": version,
        "description": "AI-assisted MARD fuse-bead portrait patterns with printable PNG/PDF output and pendant safety checks.",
        "author": {"name": "Syfyivan"},
    }


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
    output = args.output_dir / f"{SKILL_NAME}-{args.version}.zip"
    bundle_root = Path(SKILL_NAME)
    skill_root = bundle_root / "skills" / SKILL_NAME
    payload = json.dumps(manifest(args.version), ensure_ascii=False, indent=2).encode()

    with zipfile.ZipFile(output, "w") as archive:
        for destination in (bundle_root / "plugin.json", bundle_root / ".claude-plugin" / "plugin.json"):
            info = zipfile.ZipInfo(destination.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)
        for name in SKILL_FILES:
            add_path(archive, REPO_ROOT / name, skill_root / name)
        add_path(archive, REPO_ROOT / "LICENSE", bundle_root / "LICENSE")

    print(output.resolve())


if __name__ == "__main__":
    main()
