from typer.testing import CliRunner

from eliude_cli import __version__
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
    def _boom():
        raise AssertionError("maybe_warn_outdated should not run for --version")

    monkeypatch.setattr("eliude_cli.main.maybe_warn_outdated", _boom)
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
