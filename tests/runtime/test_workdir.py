from __future__ import annotations

from pathlib import Path

from npm_builder.runtime.workdir import WorkdirPaths


class TestFromWorkdir:
    def test_derives_layout_from_workdir_root(self):
        paths = WorkdirPaths.from_workdir(Path("/var/workdir"))
        assert paths == WorkdirPaths(
            workdir_root=Path("/var/workdir"),
            source_root=Path("/var/workdir/source"),
            work_root=Path("/var/workdir/work"),
            output_root=Path("/var/workdir/output"),
            artifact_root=Path("/var/workdir/artifact"),
            built_list=Path("/var/workdir/built/list.txt"),
        )

    def test_source_root_override_leaves_scratch_paths_under_workdir(self):
        paths = WorkdirPaths.from_workdir(Path("scratch"), source_root=Path("."))
        assert paths.source_root == Path(".")
        assert paths.work_root == Path("scratch/work")
        assert paths.built_list == Path("scratch/built/list.txt")


class TestAsEnv:
    def test_exports_all_paths_as_strings(self):
        paths = WorkdirPaths.from_workdir(Path("/w"), source_root=Path("/src"))
        assert paths.as_env() == {
            "WORKDIR_ROOT": "/w",
            "SOURCE_ROOT": "/src",
            "WORK_ROOT": "/w/work",
            "OUTPUT_ROOT": "/w/output",
            "ARTIFACT_ROOT": "/w/artifact",
            "BUILT_LIST": "/w/built/list.txt",
        }
