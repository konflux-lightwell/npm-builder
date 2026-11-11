from __future__ import annotations

import argparse
import logging
import subprocess  # nosec B404
from pathlib import Path

from npm_builder.build import MissingManifestError, run_build
from npm_builder.runtime.workdir import DEFAULT_WORKDIR_ROOT, WorkdirPaths

logger = logging.getLogger(__name__)


def _optional_path(value: str) -> Path | None:
    """Treat an empty argument (e.g. an unbound optional Tekton workspace) as not given."""
    return Path(value) if value else None


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("build", help="Build one or more npm package recipes")
    parser.add_argument("package_dir", nargs="+", help="Package recipe directories, relative to the source root")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=DEFAULT_WORKDIR_ROOT,
        help="Root for build scratch, outputs and the built list (default: %(default)s)",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Checkout containing the package recipes (default: <workdir>/source)",
    )
    parser.add_argument(
        "--git-auth-path",
        type=_optional_path,
        help="Directory with git credentials for cloning private sources",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    paths = WorkdirPaths.from_workdir(args.workdir, source_root=args.source_root)
    logger.debug("Building package recipes: %s", args.package_dir)
    try:
        run_build(args.package_dir, paths, git_auth_path=args.git_auth_path)
    except MissingManifestError as e:
        logger.error("%s", e)
        return 1
    except subprocess.CalledProcessError as e:
        logger.error("%s", e)
        return _exit_code(e.returncode)
    return 0


def _exit_code(returncode: int) -> int:
    """Map a subprocess return code to a shell-style exit code (128 + signal for signals)."""
    return 128 - returncode if returncode < 0 else returncode
