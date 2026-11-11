"""Build a list of npm package recipes and record which ones were built."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

from npm_builder.runtime.git_auth import configure_git
from npm_builder.runtime.workdir import WorkdirPaths
from npm_builder.tools import build_npm_package

logger = logging.getLogger(__name__)


class MissingManifestError(Exception):
    def __init__(self, manifest: Path) -> None:
        super().__init__(f"Missing manifest: {manifest}")
        self.manifest = manifest


def run_build(
    package_dirs: Sequence[str],
    paths: WorkdirPaths,
    git_auth_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Build each package recipe in order, stopping at the first failure.

    ``package_dirs`` are relative to ``paths.source_root``. Each successfully built
    package dir is appended to ``paths.built_list``, which is reset at the start.

    Raises MissingManifestError if a package has no manifest.json, and
    subprocess.CalledProcessError if its build fails.
    """
    env = os.environ if env is None else env
    base_env = {**env, **paths.as_env()}
    base_env = {**base_env, **configure_git(git_auth_path, base_env)}

    for directory in (paths.built_list.parent, paths.work_root, paths.output_root):
        directory.mkdir(parents=True, exist_ok=True)
    paths.built_list.write_text("")

    for pkg in package_dirs:
        package_dir = paths.source_root / pkg
        manifest = package_dir / "manifest.json"
        if not manifest.is_file():
            raise MissingManifestError(manifest)

        logger.info("%s", pkg)
        build_npm_package.run(
            manifest,
            env={
                **base_env,
                "WORK_DIR": str(paths.work_root / pkg),
                "OUT_DIR": str(paths.output_root / pkg),
                "PACKAGE_DIR": str(package_dir),
                "MANIFEST_PATH": str(manifest),
            },
        )
        with paths.built_list.open("a") as built_list:
            built_list.write(f"{pkg}\n")

    logger.info("Done")
