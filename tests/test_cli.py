from __future__ import annotations

from unittest.mock import patch

from npm_builder.cli import main


class TestRouting:
    def test_no_command_prints_help_and_exits_2(self, capsys):
        assert main([]) == 2
        captured = capsys.readouterr()
        assert "usage" in captured.err.lower()

    @patch("npm_builder.commands.build.run_build")
    def test_build_routes_to_run_build(self, run_build):
        assert main(["build", "pkg-a", "pkg-b"]) == 0
        assert run_build.call_args.args[0] == ["pkg-a", "pkg-b"]
