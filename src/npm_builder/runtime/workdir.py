"""Directory layout of the workdir: source checkout, build scratch, outputs and artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKDIR_ROOT = Path("/var/workdir")


@dataclass(frozen=True)
class WorkdirPaths:
    workdir_root: Path
    source_root: Path
    work_root: Path
    output_root: Path
    artifact_root: Path
    built_list: Path

    @classmethod
    def from_workdir(cls, workdir_root: Path, source_root: Path | None = None) -> WorkdirPaths:
        """Build the layout below workdir_root.

        source_root defaults to ``<workdir_root>/source`` (the Tekton trusted-artifact checkout).
        """
        return cls(
            workdir_root=workdir_root,
            source_root=workdir_root / "source" if source_root is None else source_root,
            work_root=workdir_root / "work",
            output_root=workdir_root / "output",
            artifact_root=workdir_root / "artifact",
            built_list=workdir_root / "built" / "list.txt",
        )

    def as_env(self) -> dict[str, str]:
        """Expose the layout as environment variables for build subprocesses (e.g. onboarder recipes)."""
        return {
            "WORKDIR_ROOT": str(self.workdir_root),
            "SOURCE_ROOT": str(self.source_root),
            "WORK_ROOT": str(self.work_root),
            "OUTPUT_ROOT": str(self.output_root),
            "ARTIFACT_ROOT": str(self.artifact_root),
            "BUILT_LIST": str(self.built_list),
        }
