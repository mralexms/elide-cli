from typer.testing import CliRunner

from eliude_cli.client import ApiClient, ApiError
from eliude_cli.main import app

runner = CliRunner()

CHANGE_PASSWORD_ARGS = [
    "change-password",
    "--current-password", "temp123",
    "--new-password", "hunter2hunter2",
    "--new-password-confirm", "hunter2hunter2",
]


def test_change_password_calls_the_api_and_reports_success(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")
    calls = []
    monkeypatch.setattr(ApiClient, "change_password", lambda self, *a, **kw: calls.append((a, kw)))

    result = runner.invoke(app, CHANGE_PASSWORD_ARGS)
    assert result.exit_code == 0
    assert "Password changed." in result.output
    assert calls == [(("temp123", "hunter2hunter2", "hunter2hunter2"), {})]


def test_change_password_rejects_mismatched_new_passwords_without_calling_the_api(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")
    calls = []
    monkeypatch.setattr(ApiClient, "change_password", lambda self, *a, **kw: calls.append(1))

    args = [
        "change-password",
        "--current-password", "temp123",
        "--new-password", "hunter2hunter2",
        "--new-password-confirm", "something-else",
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert "don't match" in result.output
    assert calls == []


def test_change_password_shows_api_error(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")

    def raise_error(self, *a, **kw):
        raise ApiError("Current password is incorrect.")

    monkeypatch.setattr(ApiClient, "change_password", raise_error)
    result = runner.invoke(app, CHANGE_PASSWORD_ARGS)
    assert result.exit_code == 1
    assert "Current password is incorrect." in result.output


def test_change_password_requires_login(cli_config):
    result = runner.invoke(app, CHANGE_PASSWORD_ARGS)
    assert result.exit_code == 1
    assert "Not logged in" in result.output
