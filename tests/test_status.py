import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_CLASSROOMS = [
    {"id": 1, "name": "Turma A", "slug": "turma-a"},
    {"id": 2, "name": "Turma B", "slug": "turma-b"},
]

EXERCISES_BY_CLASSROOM = {
    "turma-a": [
        {"slug": "hello-world", "status": "success"},
        {"slug": "e01", "status": "failure"},
        {"slug": "e02", "status": "pending"},
    ],
    "turma-b": [
        {"slug": "e03", "status": "success"},
    ],
}

runner = CliRunner()


@pytest.fixture
def logged_in_with_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    return cli_config


@pytest.fixture
def mock_backend(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: FAKE_CLASSROOMS)
    monkeypatch.setattr(
        ApiClient, "list_exercises", lambda self: EXERCISES_BY_CLASSROOM[self.session.headers["X-Eliude-Classroom"]]
    )


def test_status_requires_login(cli_config):
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_status_requires_active_classroom(cli_config, mock_backend):
    cli_config.set_token("faketoken123", "alice")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "No active classroom set" in result.output


def test_status_shows_login_classroom_and_counts(logged_in_with_classroom, mock_backend):
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Logged in as: alice" in result.output
    assert "Classroom: Turma A (turma-a)" in result.output
    assert "Exercises: 3" in result.output
    assert "Passed: 1" in result.output
    assert "Failed: 1" in result.output


def test_status_all_shows_every_classroom(logged_in_with_classroom, mock_backend):
    result = runner.invoke(app, ["status", "--all"])
    assert result.exit_code == 0
    assert "* Turma A (turma-a)" in result.output
    assert "  Turma B (turma-b)" in result.output
    assert "Exercises: 3" in result.output
    assert "Exercises: 1" in result.output
