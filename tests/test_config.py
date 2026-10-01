from eliude_cli import config


def test_resolve_language_alias_recognizes_known_codes():
    assert config.resolve_language_alias("pt-BR") == "pt-BR"
    assert config.resolve_language_alias("pt_br") == "pt-BR"
    assert config.resolve_language_alias("PT") == "pt-BR"
    assert config.resolve_language_alias("en") == "en"
    assert config.resolve_language_alias("EN-US") == "en"


def test_resolve_language_alias_rejects_unknown_codes():
    assert config.resolve_language_alias("fr") is None
    assert config.resolve_language_alias("klingon") is None


def test_get_language_defaults_to_configured_value(cli_config):
    cli_config.set_language("pt-BR")
    assert config.get_language() == "pt-BR"


def test_get_language_env_override_wins_over_config(cli_config, monkeypatch):
    cli_config.set_language("en")
    monkeypatch.setenv("ELIUDE_LANGUAGE", "pt-BR")
    assert config.get_language() == "pt-BR"


def test_get_language_falls_back_to_system_locale(cli_config, monkeypatch):
    monkeypatch.delenv("ELIUDE_LANGUAGE", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", "pt_BR.UTF-8")
    assert config.get_language() == "pt-BR"


def test_get_language_unrecognized_locale_falls_back_to_english(cli_config, monkeypatch):
    monkeypatch.delenv("ELIUDE_LANGUAGE", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    assert config.get_language() == "en"


def test_get_language_no_locale_info_at_all_defaults_to_english(cli_config, monkeypatch):
    monkeypatch.delenv("ELIUDE_LANGUAGE", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.delenv("LANG", raising=False)
    assert config.get_language() == "en"


def test_base_url_defaults_to_the_production_server(cli_config, monkeypatch):
    monkeypatch.delenv("ELIUDE_BASE_URL", raising=False)
    assert cli_config.get_base_url() == "https://fabrica.ifma.edu.br/eliude"


def test_configured_base_url_wins_over_the_default(cli_config, monkeypatch):
    monkeypatch.delenv("ELIUDE_BASE_URL", raising=False)
    cli_config.set_base_url("http://localhost:8000")
    assert cli_config.get_base_url() == "http://localhost:8000"
