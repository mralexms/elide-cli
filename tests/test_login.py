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
    monkeypatch.setattr(ApiClient, "login", lambda self, username, password: {"token": "newtoken"})
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


def test_failed_login_points_at_the_web_password_page(cli_config, monkeypatch):
    def bad_credentials(self, username, password):
        raise ApiError("Invalid credentials.")

    monkeypatch.setattr(ApiClient, "login", bad_credentials)
    result = login()
    assert result.exit_code == 1
    assert f"{cli_config.get_base_url()}/password/" in result.output


def test_wrong_password_gets_a_plain_message(cli_config, monkeypatch):
    def bad_credentials(self, username, password):
        raise ApiError("non_field_errors: Unable to log in with provided credentials.", status=400)

    monkeypatch.setattr(ApiClient, "login", bad_credentials)
    result = login()
    assert result.exit_code == 1
    assert "Wrong username or password." in result.output
    assert "non_field_errors" not in result.output


# --- temporary password (teacher-registered accounts) ---


@pytest.fixture
def temporary(monkeypatch, api):
    monkeypatch.setattr(
        ApiClient, "login", lambda self, username, password: {"token": "newtoken", "must_change_password": True}
    )
    state = {"changes": [], "refuse": 0}

    def change_password(self, current, new, confirm):
        state["changes"].append((current, new, confirm))
        if state["refuse"]:
            state["refuse"] -= 1
            raise ApiError("new_password: This password is too short.")

    monkeypatch.setattr(ApiClient, "change_password", change_password)
    return state


def test_temporary_password_is_replaced_right_at_login(cli_config, menus, temporary):
    menus["answers"] = ["turma-a", "lista-1"]
    result = runner.invoke(app, ["login", "--username", "alice", "--password", "secret"], input="nova-senha-1\nnova-senha-1\n")
    assert result.exit_code == 0, result.output
    assert "Your password is temporary." in result.output
    assert temporary["changes"] == [("secret", "nova-senha-1", "nova-senha-1")]
    assert menus["shown"] == ["Choose a classroom:", "Choose a practice:"]


def test_refused_new_password_asks_again(cli_config, menus, temporary):
    temporary["refuse"] = 1
    menus["answers"] = ["turma-a", "lista-1"]
    result = runner.invoke(app, ["login", "--username", "alice", "--password", "secret"], input="curta\ncurta\nnova-senha-1\nnova-senha-1\n")
    assert result.exit_code == 0, result.output
    assert "too short" in result.output
    assert [new for _, new, _ in temporary["changes"]] == ["curta", "nova-senha-1"]


def test_mismatched_new_password_is_not_sent(cli_config, menus, temporary):
    menus["answers"] = ["turma-a", "lista-1"]
    result = runner.invoke(app, ["login", "--username", "alice", "--password", "secret"], input="uma-senha-1\noutra-senha\nnova-senha-1\nnova-senha-1\n")
    assert result.exit_code == 0, result.output
    assert temporary["changes"] == [("secret", "nova-senha-1", "nova-senha-1")]


def test_gives_up_after_three_refused_passwords(cli_config, menus, temporary):
    temporary["refuse"] = 3
    result = runner.invoke(app, ["login", "--username", "alice", "--password", "secret"], input="a\na\nb\nb\nc\nc\n")
    assert result.exit_code == 0, result.output
    assert len(temporary["changes"]) == 3
    assert "eliude change-password" in result.output
    assert menus["shown"] == []
    assert cli_config.get_token() == "newtoken"


def test_temporary_password_outside_a_terminal_only_explains(cli_config, temporary, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login()
    assert result.exit_code == 0, result.output
    assert temporary["changes"] == []
    assert "eliude change-password" in result.output


def test_server_403_for_temporary_password_is_translated(cli_config, monkeypatch):
    import requests

    from eliude_cli.client import ApiClient as RealClient

    class FakeResponse:
        status_code = 403
        history = []
        text = ""

        def json(self):
            return {"detail": "You must change your temporary password...", "code": "must_change_password"}

    monkeypatch.setenv("ELIUDE_LANGUAGE", "pt")
    monkeypatch.setattr(requests.Session, "request", lambda self, method, url, **kw: FakeResponse())
    with pytest.raises(ApiError) as exc_info:
        RealClient("http://x", token="t").list_classrooms()
    assert str(exc_info.value).startswith("Você precisa trocar sua senha temporária")
