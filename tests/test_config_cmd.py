from typer.testing import CliRunner

from eliude_cli.main import app

runner = CliRunner()


def test_set_language_accepts_a_canonical_code(cli_config):
    result = runner.invoke(app, ["config", "set-language", "pt-BR"])
    assert result.exit_code == 0
    assert cli_config.get_language() == "pt-BR"
    assert "Idioma definido como pt-BR" in result.output


def test_set_language_accepts_loose_aliases(cli_config):
    result = runner.invoke(app, ["config", "set-language", "pt_br"])
    assert result.exit_code == 0
    assert cli_config.get_language() == "pt-BR"


def test_set_language_back_to_english(cli_config):
    cli_config.set_language("pt-BR")
    result = runner.invoke(app, ["config", "set-language", "en"])
    assert result.exit_code == 0
    assert cli_config.get_language() == "en"
    assert "Language set to en" in result.output


def test_set_language_rejects_unknown_code(cli_config):
    result = runner.invoke(app, ["config", "set-language", "klingon"])
    assert result.exit_code == 1
    assert "unsupported" in result.output.lower() or "suportado" in result.output.lower()
    assert cli_config.get_language() == "en"  # unchanged (falls back to default, nothing was ever set)
