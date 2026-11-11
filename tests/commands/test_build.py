from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from npm_builder.build import MissingManifestError
from npm_builder.cli import main
from npm_builder.runtime.workdir import WorkdirPaths


@pytest.fixture
def run_build():
    with patch("npm_builder.commands.build.run_build") as mock:
        yield mock


class TestArguments:
    def test_defaults(self, run_build):
        assert main(["build", "pkg-a"]) == 0
        run_build.assert_called_once_with(
            ["pkg-a"], WorkdirPaths.from_workdir(Path("/var/workdir")), git_auth_path=None
        )

    def test_explicit_paths(self, run_build):
        argv = ["build", "--workdir", "/w", "--source-root", "/src", "--git-auth-path", "/auth", "pkg-a"]
        assert main(argv) == 0
        run_build.assert_called_once_with(
            ["pkg-a"], WorkdirPaths.from_workdir(Path("/w"), source_root=Path("/src")), git_auth_path=Path("/auth")
        )

    def test_empty_git_auth_path_is_ignored(self, run_build):
        assert main(["build", "--git-auth-path", "", "pkg-a"]) == 0
        assert run_build.call_args.kwargs["git_auth_path"] is None

    def test_requires_a_package(self, run_build):
        with pytest.raises(SystemExit) as excinfo:
            main(["build"])
        assert excinfo.value.code == 2
        run_build.assert_not_called()


class TestExitCodes:
    def test_missing_manifest_exits_1(self, run_build):
        run_build.side_effect = MissingManifestError(Path("/src/pkg/manifest.json"))
        assert main(["build", "pkg"]) == 1

    def test_build_failure_exits_with_subprocess_code(self, run_build):
        run_build.side_effect = subprocess.CalledProcessError(3, "build-npm-package")
        assert main(["build", "pkg"]) == 3

    def test_build_killed_by_signal_exits_128_plus_signal(self, run_build):
        run_build.side_effect = subprocess.CalledProcessError(-9, "build-npm-package")
        assert main(["build", "pkg"]) == 137
