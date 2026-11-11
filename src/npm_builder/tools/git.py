"""Thin wrappers around the git CLI."""

from __future__ import annotations

import subprocess  # nosec B404
from collections.abc import Mapping


def config_global(key: str, value: str, env: Mapping[str, str]) -> None:
    """Run ``git config --global <key> <value>``."""
    subprocess.run(["git", "config", "--global", key, value], env=env, check=True)  # nosec B603 B607


def credential_approve(credential: str, env: Mapping[str, str]) -> None:
    """Run ``git credential approve``, feeding it a credential description on stdin."""
    subprocess.run(["git", "credential", "approve"], input=credential, text=True, env=env, check=True)  # nosec B603 B607
