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
    state = {"requested": [], "verified": [], "codes": {"482913"}}

    def request_login_code(self, login):
        state["requested"].append(login)
        return {"detail": "...", "minutes": 10}

    def verify_login_code(self, login, code):
        state["verified"].append((login, code))
        if code not in state["codes"]:
            raise ApiError("Código inválido ou expirado.", status=400)
        return {"token": "newtoken", "username": "alice"}

    monkeypatch.setattr(ApiClient, "request_login_code", request_login_code)
    monkeypatch.setattr(ApiClient, "verify_login_code", verify_login_code)
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: CLASSROOMS)
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: PRACTICES)
    monkeypatch.setattr(ApiClient, "start_practice", lambda self, slug: {"attempt": None})
    return state


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


def login(*extra, input="482913\n"):
    return runner.invoke(app, ["login", "--login", "alice@example.com", *extra], input=input)


def test_login_emails_a_code_and_trades_it_for_a_token(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login()
    assert result.exit_code == 0, result.output
    assert api["requested"] == ["alice@example.com"]
    assert api["verified"] == [("alice@example.com", "482913")]
    assert "we sent a 6-digit code to its email. It's valid for 10 minutes." in result.output
    assert f"{cli_config.get_base_url()}/cli-code/" in result.output
    assert "Logged in as alice." in result.output
    # O usuário salvo é o que o servidor devolve, não o email digitado.
    assert cli_config.get_token() == "newtoken"
    assert cli_config.get_username() == "alice"


def test_asks_for_the_login_when_not_given(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = runner.invoke(app, ["login"], input="alice\n482913\n")
    assert result.exit_code == 0, result.output
    assert "Email or username" in result.output
    assert api["requested"] == ["alice"]


def test_a_wrong_code_can_be_typed_again(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login(input="111111\n482913\n")
    assert result.exit_code == 0, result.output
    assert "Invalid or expired code." in result.output
    assert [code for _, code in api["verified"]] == ["111111", "482913"]


def test_gives_up_after_three_wrong_codes(cli_config, api):
    result = login(input="1\n2\n3\n")
    assert result.exit_code == 1
    assert len(api["verified"]) == 3
    assert "Run `eliude login` again" in result.output
    assert cli_config.get_token() is None


def test_a_code_given_up_front_skips_the_email(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login("--code", "482913", input="")
    assert result.exit_code == 0, result.output
    assert api["requested"] == []
    assert cli_config.get_token() == "newtoken"


def test_a_wrong_code_given_up_front_is_not_asked_again(cli_config, api):
    result = login("--code", "000000", input="")
    assert result.exit_code == 1
    assert len(api["verified"]) == 1


def test_no_email_asks_for_a_web_code_without_sending_one(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login("--no-email")
    assert result.exit_code == 0, result.output
    assert api["requested"] == []
    assert api["verified"] == [("alice@example.com", "482913")]


def test_email_unavailable_points_at_the_web_code(cli_config, api, monkeypatch):
    def unavailable(self, login):
        raise ApiError("The Eliude server ran into an error (HTTP 503).", status=503)

    monkeypatch.setattr(ApiClient, "request_login_code", unavailable)
    result = login()
    assert result.exit_code == 1
    assert "Couldn't send the email right now." in result.output
    assert "eliude login --no-email" in result.output
    assert api["verified"] == []


def test_other_request_errors_are_shown_as_is(cli_config, api, monkeypatch):
    def throttled(self, login):
        raise ApiError("Too many requests. Wait a moment and try again.")

    monkeypatch.setattr(ApiClient, "request_login_code", throttled)
    result = login()
    assert result.exit_code == 1
    assert "Too many requests." in result.output


def test_portuguese_messages(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setenv("ELIUDE_LANGUAGE", "pt")
    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login(input="111111\n482913\n")
    assert result.exit_code == 0, result.output
    assert "enviamos um código de 6 dígitos" in result.output
    assert "Código inválido ou expirado." in result.output


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


def test_login_outside_a_terminal_opens_no_menus(cli_config, api, monkeypatch):
    from eliude_cli import prompts

    monkeypatch.setattr(prompts, "is_interactive", lambda: False)
    result = login()
    assert result.exit_code == 0
    assert result.output.strip().endswith("Logged in as alice.")
    assert cli_config.get_active_classroom() is None


def test_failed_login_opens_no_menus(cli_config, api, menus):
    result = login(input="1\n2\n3\n")
    assert result.exit_code == 1
    assert menus["shown"] == []


def test_client_sends_the_login_and_the_code(monkeypatch):
    import requests

    from eliude_cli.client import ApiClient as RealClient

    calls = []

    class FakeResponse:
        status_code = 200
        history = []
        text = ""

        def json(self):
            return {"token": "t", "username": "alice"}

    def fake_request(self, method, url, **kw):
        calls.append((method, url, kw.get("data")))
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "request", fake_request)
    client = RealClient("http://x")
    client.request_login_code("alice")
    client.verify_login_code("alice", "123456")
    assert calls == [
        ("POST", "http://x/api/auth/code/", {"login": "alice"}),
        ("POST", "http://x/api/auth/code/verify/", {"login": "alice", "code": "123456"}),
    ]


def test_a_server_error_keeps_its_status(monkeypatch):
    import requests

    from eliude_cli.client import ApiClient as RealClient

    class FakeResponse:
        status_code = 503
        history = []
        text = ""

    monkeypatch.setattr(requests.Session, "request", lambda self, method, url, **kw: FakeResponse())
    with pytest.raises(ApiError) as exc_info:
        RealClient("http://x").request_login_code("alice")
    assert exc_info.value.status == 503
