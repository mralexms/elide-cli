from eliude_cli.messages import t


def test_t_returns_english_by_default(cli_config):
    assert t("session.not_logged_in") == "Not logged in. Run `eliude login` first."


def test_t_returns_pt_br_when_configured(cli_config):
    cli_config.set_language("pt-BR")
    assert t("session.not_logged_in") == "Você não está logado. Rode `eliude login` primeiro."


def test_t_formats_placeholders(cli_config):
    assert t("classrooms.switched", name="Turma A", slug="turma-a") == "Switched to classroom 'Turma A' (turma-a)."


def test_t_falls_back_to_english_for_a_key_missing_in_the_current_language(cli_config, monkeypatch):
    from eliude_cli import messages

    cli_config.set_language("pt-BR")
    monkeypatch.delitem(messages._MESSAGES["pt-BR"], "session.not_logged_in")
    assert t("session.not_logged_in") == "Not logged in. Run `eliude login` first."


def test_t_returns_the_key_itself_if_missing_everywhere(cli_config):
    assert t("does.not.exist") == "does.not.exist"


def test_every_english_key_has_a_pt_br_translation():
    from eliude_cli.messages import _MESSAGES

    missing = set(_MESSAGES["en"]) - set(_MESSAGES["pt-BR"])
    assert missing == set()


def test_every_pt_br_key_exists_in_english():
    from eliude_cli.messages import _MESSAGES

    extra = set(_MESSAGES["pt-BR"]) - set(_MESSAGES["en"])
    assert extra == set()
