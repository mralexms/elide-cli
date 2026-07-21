import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_CLASSROOMS = [
    {"id": 1, "name": "Turma A", "slug": "turma-a"},
    {"id": 2, "name": "Turma B", "slug": "turma-b"},
]


@pytest.fixture
def logged_in(cli_config):
    cli_config.set_token("faketoken123", "alice")
    return cli_config


@pytest.fixture
def mock_classrooms(monkeypatch):
    def fake_list_classrooms(self):
        return FAKE_CLASSROOMS

    monkeypatch.setattr(ApiClient, "list_classrooms", fake_list_classrooms)


def test_classrooms_list_requires_login(cli_config):
    result = runner.invoke(app, ["classrooms", "list"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_switch_requires_login(cli_config):
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_classrooms_list_none_active(logged_in, mock_classrooms):
    result = runner.invoke(app, ["classrooms", "list"])
    assert result.exit_code == 0
    assert "  turma-a" in result.output
    assert "  turma-b" in result.output
    assert "*" not in result.output


def test_classrooms_list_marks_active(logged_in, mock_classrooms):
    logged_in.set_active_classroom("turma-b")
    result = runner.invoke(app, ["classrooms", "list"])
    assert result.exit_code == 0
    assert "* turma-b" in result.output
    assert "  turma-a" in result.output


def test_switch_no_arg_lists_same_as_classrooms_list(logged_in, mock_classrooms):
    logged_in.set_active_classroom("turma-a")
    switch_result = runner.invoke(app, ["switch"])
    list_result = runner.invoke(app, ["classrooms", "list"])
    assert switch_result.exit_code == 0
    assert switch_result.output == list_result.output


def test_switch_with_valid_slug_sets_active(logged_in, mock_classrooms):
    result = runner.invoke(app, ["switch", "turma-b"])
    assert result.exit_code == 0
    assert "Switched to classroom 'Turma B' (turma-b)." in result.output
    assert logged_in.get_active_classroom() == "turma-b"


def test_switch_with_invalid_slug_fails_without_changing_config(logged_in, mock_classrooms):
    logged_in.set_active_classroom("turma-a")
    result = runner.invoke(app, ["switch", "does-not-exist"])
    assert result.exit_code == 1
    assert "not enrolled in classroom 'does-not-exist'" in result.output
    assert logged_in.get_active_classroom() == "turma-a"


def test_switch_with_no_classrooms_enrolled(logged_in, monkeypatch):
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: [])
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "not enrolled in any classrooms" in result.output


def test_classrooms_list_with_no_classrooms_enrolled(logged_in, monkeypatch):
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: [])
    result = runner.invoke(app, ["classrooms", "list"])
    assert result.exit_code == 1
    assert "not enrolled in any classrooms" in result.output
