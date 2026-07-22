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
