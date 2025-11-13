#!/usr/bin/env python3
"""Simple helper to bump the project version inside ``pyproject.toml``.

The script focuses on semantic version numbers made of ``MAJOR.MINOR.PATCH``.
By default it increments the patch component, updates the ``pyproject.toml``
file in place, and prints the new version so that automation workflows can
capture it.
"""
from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
VERSION_PATTERN = re.compile(r'^(version\s*=\s*")(\d+)\.(\d+)\.(\d+)("\s*)$', re.MULTILINE)


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    def bump(self, release_type: str) -> "Version":
        if release_type == "major":
            return Version(self.major + 1, 0, 0)
        if release_type == "minor":
            return Version(self.major, self.minor + 1, 0)
        if release_type == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unsupported release type: {release_type}")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return f"{self.major}.{self.minor}.{self.patch}"


def load_version() -> Version:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(content)
    if not match:
        raise RuntimeError("Unable to find version in pyproject.toml")
    return Version(*(int(group) for group in match.groups()[1:4]))


def update_version(new_version: Version) -> None:
    original = PYPROJECT.read_text(encoding="utf-8")
    replaced, count = VERSION_PATTERN.subn(
        lambda m: f'{m.group(1)}{new_version}{m.group(5)}', original, count=1
    )
    if count != 1:
        raise RuntimeError("Expected to update exactly one version string")
    PYPROJECT.write_text(replaced, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Which component of the semantic version to bump (default: patch)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Calculate the next version without updating pyproject.toml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    current = load_version()
    new_version = current.bump(args.release_type)
    if not args.no_write:
        update_version(new_version)
    print(new_version)


if __name__ == "__main__":
    main()
