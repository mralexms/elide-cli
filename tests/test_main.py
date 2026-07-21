from typer.testing import CliRunner

from eliude_cli import __version__
from eliude_cli.main import app

runner = CliRunner()


def test_bare_invocation_shows_version_and_help(cli_config):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "Usage: eliude" in result.output
