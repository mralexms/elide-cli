from typer.testing import CliRunner

from eliude_cli.client import ApiClient, ApiError
from eliude_cli.main import app

runner = CliRunner()

SIGNUP_ARGS = [
    "signup",
    "--name", "Nova Aluna",
    "--email", "nova@example.com",
    "--password", "hunter2hunter2",
    "--password-confirm", "hunter2hunter2",
    "--classroom-code", "ABC123",
]

FAKE_RESULT = {"token": "faketoken123", "classroom": {"slug": "turma-a", "name": "Turma A"}}


def test_signup_stores_token_and_switches_to_the_joined_classroom(cli_config, monkeypatch):
    monkeypatch.setattr(ApiClient, "signup", lambda self, *a, **kw: FAKE_RESULT)

    result = runner.invoke(app, SIGNUP_ARGS)
    assert result.exit_code == 0
    assert "Turma A" in result.output
    assert cli_config.get_token() == "faketoken123"
    assert cli_config.get_username() == "nova@example.com"
    assert cli_config.get_active_classroom() == "turma-a"


def test_signup_forwards_all_fields_to_the_client(cli_config, monkeypatch):
    captured = {}

    def fake_signup(self, name, email, password, password_confirm, classroom_code):
        captured.update(
            name=name, email=email, password=password, password_confirm=password_confirm,
            classroom_code=classroom_code,
        )
        return FAKE_RESULT

    monkeypatch.setattr(ApiClient, "signup", fake_signup)
    runner.invoke(app, SIGNUP_ARGS)
    assert captured == {
        "name": "Nova Aluna",
        "email": "nova@example.com",
        "password": "hunter2hunter2",
        "password_confirm": "hunter2hunter2",
        "classroom_code": "ABC123",
    }


def test_signup_rejects_mismatched_passwords_without_calling_the_api(cli_config, monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "signup", lambda self, *a, **kw: calls.append(1))

    args = [
        "signup",
        "--name", "Nova Aluna",
        "--email", "nova@example.com",
        "--password", "hunter2hunter2",
        "--password-confirm", "something-else",
        "--classroom-code", "ABC123",
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert "don't match" in result.output
    assert calls == []


def test_signup_shows_api_error_and_does_not_store_a_token(cli_config, monkeypatch):
    def raise_error(self, *a, **kw):
        raise ApiError("Invalid classroom code.")

    monkeypatch.setattr(ApiClient, "signup", raise_error)
    result = runner.invoke(app, SIGNUP_ARGS)
    assert result.exit_code == 1
    assert "Invalid classroom code." in result.output
    assert cli_config.get_token() is None
