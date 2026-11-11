from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from npm_builder.tools import build_npm_package


@patch("npm_builder.tools.build_npm_package.subprocess.run")
def test_run(run):
    env = {"PATH": "/usr/bin"}
    build_npm_package.run(Path("/src/pkg/manifest.json"), env=env)
    run.assert_called_once_with(["build-npm-package", "--manifest", "/src/pkg/manifest.json"], env=env, check=True)
