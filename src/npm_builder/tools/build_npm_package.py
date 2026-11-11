"""Thin wrapper around the build-npm-package recipe runner."""

from __future__ import annotations

import subprocess  # nosec B404
from collections.abc import Mapping
from pathlib import Path


def run(manifest: Path, env: Mapping[str, str]) -> None:
    """Run ``build-npm-package --manifest <manifest>``."""
    subprocess.run(["build-npm-package", "--manifest", str(manifest)], env=env, check=True)  # nosec B603 B607
