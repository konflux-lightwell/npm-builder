from __future__ import annotations

import argparse
import logging

from npm_builder.build import run_build

logger = logging.getLogger(__name__)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("build", help="Build one or more npm package recipes")
    parser.add_argument("package_dir", nargs="+", help="Path(s) to package recipe directories")
    parser.add_argument("--workdir", help="Override the factory working directory root")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    logger.debug("Building package recipes: %s", args.package_dir)
    run_build(args.package_dir, workdir=args.workdir)
    return 0
