import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_CLASSROOMS = [
    {"id": 1, "name": "Turma A", "slug": "turma-a"},
    {"id": 2, "name": "Turma B", "slug": "turma-b"},
]

PRACTICES_BY_CLASSROOM = {
    "turma-a": [{"slug": "turma-a-exercicios", "title": "Exercícios"}],
    "turma-b": [{"slug": "turma-b-exercicios", "title": "Exercícios"}],
}

QUESTIONS_BY_PRACTICE = {
    "turma-a-exercicios": [
        {"slug": "q1", "status": "success"},
        {"slug": "q2", "status": "failure"},
        {"slug": "q3", "status": "pending"},
    ],
    "turma-b-exercicios": [
        {"slug": "q1", "status": "success"},
    ],
}


@pytest.fixture
def logged_in_with_practice(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    cli_config.set_active_practice("turma-a-exercicios")
    return cli_config


@pytest.fixture
def mock_backend(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: FAKE_CLASSROOMS)
    monkeypatch.setattr(
        ApiClient, "list_practices", lambda self: PRACTICES_BY_CLASSROOM[self.session.headers["X-Eliude-Classroom"]]
    )
    monkeypatch.setattr(
        ApiClient,
        "list_questions",
        lambda self, tag=None: QUESTIONS_BY_PRACTICE[self.session.headers["X-Eliude-Practice"]],
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


def test_status_requires_active_practice(cli_config, mock_backend):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "No active practice set" in result.output


def test_status_shows_login_classroom_and_counts(logged_in_with_practice, mock_backend):
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Logged in as: alice" in result.output
    assert "Classroom: Turma A (turma-a)" in result.output
    assert "Practice: turma-a-exercicios" in result.output
    assert "Questions: 3" in result.output
    assert "Passed: 1" in result.output
    assert "Failed: 1" in result.output
    assert "Score: 33.3% (1/3)" in result.output


def test_status_all_shows_every_classroom_and_practice(logged_in_with_practice, mock_backend):
    result = runner.invoke(app, ["status", "--all"])
    assert result.exit_code == 0
    assert "* Turma A (turma-a)" in result.output
    assert "  Turma B (turma-b)" in result.output
    assert "Exercícios (turma-a-exercicios)" in result.output
    assert "Exercícios (turma-b-exercicios)" in result.output
    assert "Score: 33.3% (1/3)" in result.output
    assert "Score: 100.0% (1/1)" in result.output
