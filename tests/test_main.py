import pytest
from typer.testing import CliRunner

from eliude_cli import __version__, main as main_module, version_check
from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()


def test_bare_invocation_shows_version_and_help(cli_config):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "Usage: eliude" in result.output


def test_version_flag_prints_version_only(cli_config):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"eliude {__version__}"
    assert "Usage: eliude" not in result.output


def test_version_flag_skips_version_check_network_call(cli_config, monkeypatch):
    def _boom(ctx):
        raise AssertionError("check_version_compatibility should not run for --version")

    monkeypatch.setattr("eliude_cli.main.check_version_compatibility", _boom)
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0


def test_incompatible_version_blocks_a_real_command(cli_config, monkeypatch):
    monkeypatch.setattr(main_module, "check_version_compatibility", version_check.check_version_compatibility)
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "999.0.0", "repo_url": "https://x"}
    )
    result = runner.invoke(app, ["classrooms", "list"])
    assert result.exit_code == 1
    assert "requires eliude-cli 999.0.0" in result.output


def test_incompatible_version_does_not_block_config(cli_config, monkeypatch):
    monkeypatch.setattr(main_module, "check_version_compatibility", version_check.check_version_compatibility)
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "999.0.0", "repo_url": "https://x"}
    )
    result = runner.invoke(app, ["config", "set-url", "http://example.com"])
    assert result.exit_code == 0


def test_incompatible_version_does_not_block_a_subcommands_help(cli_config, monkeypatch):
    monkeypatch.setattr(main_module, "check_version_compatibility", version_check.check_version_compatibility)
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "999.0.0", "repo_url": "https://x"}
    )
    result = runner.invoke(app, ["classrooms", "--help"])
    assert result.exit_code == 0
    assert "requires eliude-cli" not in result.output
    assert "Usage: eliude classrooms" in result.output


def test_incompatible_version_does_not_block_a_nested_subcommands_help(cli_config, monkeypatch):
    monkeypatch.setattr(main_module, "check_version_compatibility", version_check.check_version_compatibility)
    monkeypatch.setattr(
        ApiClient, "get_latest_release", lambda self: {"version": "999.0.0", "repo_url": "https://x"}
    )
    result = runner.invoke(app, ["questions", "show", "--help"])
    assert result.exit_code == 0
    assert "requires eliude-cli" not in result.output
    assert "Usage: eliude questions show" in result.output


def test_invalid_top_level_command_shows_root_help_not_generic_error(cli_config):
    result = runner.invoke(app, ["foobar"])
    assert result.exit_code == 2
    assert "Usage: eliude" in result.output
    assert "questions" in result.output  # a real subcommand is listed
    assert "No such command" not in result.output


def test_invalid_nested_command_shows_that_group_help(cli_config):
    result = runner.invoke(app, ["questions", "foobar"])
    assert result.exit_code == 2
    assert "Usage: eliude questions" in result.output
    assert "list" in result.output  # questions' own subcommand is listed
    assert "No such command" not in result.output


def test_run_turns_an_unhandled_exception_into_a_short_message(cli_config, monkeypatch, capsys):
    def boom():
        raise RuntimeError("internal detail")

    monkeypatch.delenv("ELIUDE_DEBUG", raising=False)
    monkeypatch.setattr(main_module, "app", boom)
    with pytest.raises(SystemExit) as exc_info:
        main_module.run()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Something went wrong" in err
    assert "internal detail" not in err
    assert "Traceback" not in err


def test_run_shows_the_traceback_with_eliude_debug(cli_config, monkeypatch):
    def boom():
        raise RuntimeError("internal detail")

    monkeypatch.setenv("ELIUDE_DEBUG", "1")
    monkeypatch.setattr(main_module, "app", boom)
    with pytest.raises(RuntimeError, match="internal detail"):
        main_module.run()
