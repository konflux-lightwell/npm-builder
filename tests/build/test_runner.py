from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from npm_builder.build import MissingManifestError, run_build
from npm_builder.runtime.workdir import WorkdirPaths


@pytest.fixture
def paths(tmp_path: Path) -> WorkdirPaths:
    paths = WorkdirPaths.from_workdir(tmp_path / "workdir", source_root=tmp_path / "source")
    for pkg in ("packages/a/1.0.0", "packages/b/2.0.0"):
        (paths.source_root / pkg).mkdir(parents=True)
        (paths.source_root / pkg / "manifest.json").write_text("{}")
    return paths


@pytest.fixture(autouse=True)
def configure_git():
    with patch("npm_builder.build.runner.configure_git", return_value={"GIT_CONFIG_GLOBAL": "/tmp/gitconfig"}) as mock:
        yield mock


@pytest.fixture
def build_package():
    with patch("npm_builder.build.runner.build_npm_package.run") as mock:
        yield mock


class TestRunBuild:
    def test_builds_packages_in_order_and_records_them(self, paths, build_package):
        run_build(["packages/a/1.0.0", "packages/b/2.0.0"], paths, env={})

        manifests = [call.args[0] for call in build_package.call_args_list]
        assert manifests == [
            paths.source_root / "packages/a/1.0.0/manifest.json",
            paths.source_root / "packages/b/2.0.0/manifest.json",
        ]
        assert paths.built_list.read_text() == "packages/a/1.0.0\npackages/b/2.0.0\n"

    def test_creates_scratch_directories(self, paths, build_package):
        run_build(["packages/a/1.0.0"], paths, env={})

        assert paths.work_root.is_dir()
        assert paths.output_root.is_dir()

    def test_package_env(self, paths, build_package):
        run_build(["packages/a/1.0.0"], paths, env={"PATH": "/usr/bin"})

        pkg = "packages/a/1.0.0"
        assert build_package.call_args.kwargs["env"] == {
            "PATH": "/usr/bin",
            **paths.as_env(),
            "GIT_CONFIG_GLOBAL": "/tmp/gitconfig",
            "WORK_DIR": str(paths.work_root / pkg),
            "OUT_DIR": str(paths.output_root / pkg),
            "PACKAGE_DIR": str(paths.source_root / pkg),
            "MANIFEST_PATH": str(paths.source_root / pkg / "manifest.json"),
        }

    def test_passes_git_auth_path_and_base_env_to_configure_git(self, paths, build_package, configure_git):
        run_build(["packages/a/1.0.0"], paths, git_auth_path=Path("/auth"), env={"PATH": "/usr/bin"})

        configure_git.assert_called_once_with(Path("/auth"), {"PATH": "/usr/bin", **paths.as_env()})

    def test_resets_existing_built_list(self, paths, build_package):
        paths.built_list.parent.mkdir(parents=True)
        paths.built_list.write_text("stale\n")

        run_build(["packages/a/1.0.0"], paths, env={})

        assert paths.built_list.read_text() == "packages/a/1.0.0\n"

    def test_missing_manifest_stops_and_keeps_earlier_packages(self, paths, build_package):
        with pytest.raises(MissingManifestError) as excinfo:
            run_build(["packages/a/1.0.0", "packages/missing", "packages/b/2.0.0"], paths, env={})

        assert excinfo.value.manifest == paths.source_root / "packages/missing/manifest.json"
        assert build_package.call_count == 1
        assert paths.built_list.read_text() == "packages/a/1.0.0\n"

    def test_build_failure_stops_and_keeps_earlier_packages(self, paths, build_package):
        build_package.side_effect = [None, subprocess.CalledProcessError(3, "build-npm-package")]

        with pytest.raises(subprocess.CalledProcessError):
            run_build(["packages/a/1.0.0", "packages/b/2.0.0"], paths, env={})

        assert paths.built_list.read_text() == "packages/a/1.0.0\n"
