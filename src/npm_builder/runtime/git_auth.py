"""Git trust and credentials for cloning private sources.

Picks up the corporate CA bundle mounted in the build environment and, when a
git-auth directory is provided, sets up an isolated global git config with a
credential store. Nothing is written to the user's HOME.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from npm_builder.tools import git

logger = logging.getLogger(__name__)

CA_BUNDLE_CANDIDATES = (
    Path("/mnt/trusted-ca/ca-bundle.crt"),
    Path("/etc/pki/tls/certs/ca-custom-bundle.crt"),
)
CREDENTIALS_HOST = "gitlab.cee.redhat.com"


def configure_git(
    git_auth_path: Path | None,
    env: Mapping[str, str],
    ca_bundles: Sequence[Path] = CA_BUNDLE_CANDIDATES,
) -> dict[str, str]:
    """Configure git trust and credentials; return the env vars git needs to use them.

    ``git_auth_path`` is a directory holding either a ``.git-credentials`` file or
    ``username`` and ``password`` files, plus an optional ``.gitconfig``. It is
    ignored when unset or not a directory. ``env`` is the base environment for
    the git commands run here.
    """
    extra_env: dict[str, str] = {}

    ca_bundle = _find_ca_bundle(ca_bundles)
    if ca_bundle:
        extra_env["GIT_SSL_CAINFO"] = str(ca_bundle)
        extra_env["SSL_CERT_FILE"] = str(ca_bundle)
        logger.info("using CA bundle %s", ca_bundle)

    if not git_auth_path or not git_auth_path.is_dir():
        return extra_env

    config_dir = Path(tempfile.mkdtemp())  # created with mode 0700
    git_config = config_dir / ".gitconfig"
    creds_file = config_dir / ".git-credentials"
    extra_env["GIT_CONFIG_GLOBAL"] = str(git_config)
    git_env = {**env, **extra_env}

    if (git_auth_path / ".gitconfig").is_file():
        shutil.copyfile(git_auth_path / ".gitconfig", git_config)
    # Pin the store to our file, overriding any helper from the copied .gitconfig.
    git.config_global("credential.helper", f"store --file={creds_file}", env=git_env)

    if (git_auth_path / ".git-credentials").is_file():
        shutil.copyfile(git_auth_path / ".git-credentials", creds_file)
        logger.info("configured git credentials from git-auth workspace")
        return extra_env

    username_file = git_auth_path / "username"
    password_file = git_auth_path / "password"
    if username_file.is_file() and password_file.is_file():
        username = username_file.read_text().replace("\n", "")
        password = password_file.read_text().replace("\n", "")
        git.credential_approve(
            f"protocol=https\nhost={CREDENTIALS_HOST}\nusername={username}\npassword={password}\n\n",
            env=git_env,
        )
        logger.info("configured git credentials from username/password")

    return extra_env


def _find_ca_bundle(candidates: Sequence[Path]) -> Path | None:
    """Return the first candidate that exists and is non-empty."""
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None
