from __future__ import annotations

from unittest.mock import patch

from npm_builder.tools import git


@patch("npm_builder.tools.git.subprocess.run")
def test_config_global(run):
    env = {"PATH": "/usr/bin"}
    git.config_global("credential.helper", "store", env=env)
    run.assert_called_once_with(["git", "config", "--global", "credential.helper", "store"], env=env, check=True)


@patch("npm_builder.tools.git.subprocess.run")
def test_credential_approve_feeds_stdin(run):
    env = {"PATH": "/usr/bin"}
    git.credential_approve("protocol=https\nhost=example.com\n\n", env=env)
    run.assert_called_once_with(
        ["git", "credential", "approve"],
        input="protocol=https\nhost=example.com\n\n",
        text=True,
        env=env,
        check=True,
    )
