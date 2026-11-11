from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from npm_builder.runtime.git_auth import configure_git

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@pytest.fixture
def base_env() -> dict[str, str]:
    """Process env without any git configuration leaking in from the host."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


@pytest.fixture
def auth_dir(tmp_path: Path) -> Path:
    path = tmp_path / "git-auth"
    path.mkdir()
    return path


def git_config_get(env: dict[str, str], key: str) -> str:
    result = subprocess.run(["git", "config", "--global", key], env=env, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class TestCaBundle:
    def test_first_non_empty_candidate_wins(self, tmp_path, base_env):
        empty = tmp_path / "empty.crt"
        empty.touch()
        first = tmp_path / "first.crt"
        first.write_text("cert")
        second = tmp_path / "second.crt"
        second.write_text("cert")

        extra = configure_git(None, base_env, ca_bundles=[tmp_path / "missing.crt", empty, first, second])

        assert extra == {"GIT_SSL_CAINFO": str(first), "SSL_CERT_FILE": str(first)}

    def test_no_bundle_found(self, tmp_path, base_env):
        assert configure_git(None, base_env, ca_bundles=[tmp_path / "missing.crt"]) == {}


class TestGitAuth:
    def test_ignored_when_path_is_not_a_directory(self, tmp_path, base_env):
        assert configure_git(tmp_path / "missing", base_env, ca_bundles=[]) == {}

    @requires_git
    def test_pins_credential_store_over_copied_gitconfig(self, auth_dir, base_env):
        (auth_dir / ".gitconfig").write_text("[credential]\n\thelper = cache\n[user]\n\tname = Bot\n")

        extra = configure_git(auth_dir, base_env, ca_bundles=[])

        git_config = Path(extra["GIT_CONFIG_GLOBAL"])
        creds_file = git_config.parent / ".git-credentials"
        env = {**base_env, **extra}
        assert git_config_get(env, "user.name") == "Bot"
        assert git_config_get(env, "credential.helper") == f"store --file={creds_file}"
        assert git_config.parent.stat().st_mode & 0o777 == 0o700

    @requires_git
    def test_copies_git_credentials_file(self, auth_dir, base_env):
        (auth_dir / ".git-credentials").write_text("https://u:p@example.com\n")
        (auth_dir / "username").write_text("ignored")
        (auth_dir / "password").write_text("ignored")

        extra = configure_git(auth_dir, base_env, ca_bundles=[])

        creds_file = Path(extra["GIT_CONFIG_GLOBAL"]).parent / ".git-credentials"
        assert creds_file.read_text() == "https://u:p@example.com\n"

    @requires_git
    def test_stores_username_and_password(self, auth_dir, base_env):
        (auth_dir / "username").write_text("bot\n")
        (auth_dir / "password").write_text("p@ss\n")

        extra = configure_git(auth_dir, base_env, ca_bundles=[])

        creds_file = Path(extra["GIT_CONFIG_GLOBAL"]).parent / ".git-credentials"
        assert creds_file.read_text() == "https://bot:p%40ss@gitlab.cee.redhat.com\n"

    @requires_git
    def test_no_credentials_still_pins_store(self, auth_dir, base_env):
        extra = configure_git(auth_dir, base_env, ca_bundles=[])

        git_config = Path(extra["GIT_CONFIG_GLOBAL"])
        assert git_config_get({**base_env, **extra}, "credential.helper").startswith("store --file=")
        assert not (git_config.parent / ".git-credentials").exists()

    @requires_git
    def test_ca_and_auth_env_are_combined(self, tmp_path, auth_dir, base_env):
        ca = tmp_path / "ca.crt"
        ca.write_text("cert")

        extra = configure_git(auth_dir, base_env, ca_bundles=[ca])

        assert set(extra) == {"GIT_SSL_CAINFO", "SSL_CERT_FILE", "GIT_CONFIG_GLOBAL"}
