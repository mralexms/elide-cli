from typer.testing import CliRunner

from eliude_cli.client import ApiClient, ApiError
from eliude_cli.main import app

runner = CliRunner()


def test_logout_calls_api_and_clears_local_state(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")

    calls = []
    monkeypatch.setattr(ApiClient, "logout", lambda self: calls.append(1))

    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert calls == [1]
    assert cli_config.get_token() is None
    assert cli_config.get_active_classroom() is None


def test_logout_clears_local_state_even_if_api_call_fails(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")

    def raise_error(self):
        raise ApiError("offline")

    monkeypatch.setattr(ApiClient, "logout", raise_error)

    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert cli_config.get_token() is None


def test_logout_without_a_stored_token_does_not_call_the_api(cli_config, monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "logout", lambda self: calls.append(1))

    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert calls == []


# --- menus right after a successful login ---

import pytest  # noqa: E402

CLASSROOMS = [{"id": 1, "name": "Turma A", "slug": "turma-a"}]
PRACTICES = [
    {"slug": "lista-1", "title": "Lista 1", "is_timed": False, "duration_minutes": None, "window_status": "open", "attempt": None},
]


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(ApiClient, "login", lambda self, username, password: "newtoken")
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: CLASSROOMS)
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: PRACTICES)
    monkeypatch.setattr(ApiClient, "start_practice", lambda self, slug: {"attempt": None})


@pytest.fixture
def menus(monkeypatch):
    from eliude_cli import prompts

    state = {"answers": [], "shown": []}

    def fake_select(message, options, default=None):
        state["shown"].append(message)
        return state["answers"].pop(0)

    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "select", fake_select)
    return state


def login(*extra):
    return runner.invoke(app, ["login", "--username", "alice", "--password", "secret", *extra])


def test_login_goes_straight_into_classroom_and_practice_menus(cli_config, api, menus):
    menus["answers"] = ["turma-a", "lista-1"]
    result = login()
    assert result.exit_code == 0, result.output
    assert menus["shown"] == ["Choose a classroom:", "Choose a practice:"]
    assert "Logged in as alice." in result.output
    assert cli_config.get_active_classroom() == "turma-a"
    assert cli_config.get_active_practice() == "lista-1"


def test_cancelling_the_menu_after_login_keeps_the_login(cli_config, api, menus):
    menus["answers"] = [None]
    result = login()
    assert result.exit_code == 0, result.output
    assert cli_config.get_token() == "newtoken"
    assert "You can choose your classroom and practice later with `eliude switch`." in result.output


def test_temporary_password_after_login_explains_instead_of_failing(cli_config, api, menus, monkeypatch):
    def forbidden(self):
        raise ApiError("You must change your temporary password before continuing. Run `eliude change-password`.")

    monkeypatch.setattr(ApiClient, "list_classrooms", forbidden)
    result = login()
    assert result.exit_code == 0, result.output
    assert menus["shown"] == []
    assert "eliude change-password" in result.output
    assert cli_config.get_token() == "newtoken"


def test_login_outside_a_terminal_opens_no_menus(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login()
    assert result.exit_code == 0
    assert result.output.strip() == "Logged in as alice."
    assert cli_config.get_active_classroom() is None


def test_failed_login_opens_no_menus(cli_config, menus, monkeypatch):
    def bad_credentials(self, username, password):
        raise ApiError("Invalid credentials.")

    monkeypatch.setattr(ApiClient, "login", bad_credentials)
    result = login()
    assert result.exit_code == 1
    assert menus["shown"] == []
