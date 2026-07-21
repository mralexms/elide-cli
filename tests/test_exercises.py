import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_EXERCISES = [
    {
        "slug": "hello-world",
        "title": "Hello World",
        "difficulty": "easy",
        "status": "success",
        "last_submission_at": "2026-07-21T15:26:27.257941Z",
    },
    {
        "slug": "sum-two-numbers",
        "title": "Sum Two Numbers",
        "difficulty": "easy",
        "status": "pending",
        "last_submission_at": None,
    },
    {
        "slug": "broken-attempt",
        "title": "Broken Attempt",
        "difficulty": "easy",
        "status": "failure",
        "last_submission_at": "2026-07-21T16:00:00.000000Z",
    },
]


@pytest.fixture
def logged_in_with_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    return cli_config


@pytest.fixture
def mock_exercises(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_exercises", lambda self: FAKE_EXERCISES)


def test_list_requires_login(cli_config):
    result = runner.invoke(app, ["exercises", "list"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_list_shows_status_for_each_exercise(logged_in_with_classroom, mock_exercises):
    result = runner.invoke(app, ["exercises", "list"])
    assert result.exit_code == 0
    assert "hello-world" in result.output
    assert "success" in result.output
    assert "sum-two-numbers" in result.output
    assert "pending" in result.output


def test_list_hides_timestamp_by_default(logged_in_with_classroom, mock_exercises):
    result = runner.invoke(app, ["exercises", "list"])
    assert result.exit_code == 0
    assert "last submitted" not in result.output


def test_list_shows_timestamp_with_flag(logged_in_with_classroom, mock_exercises):
    result = runner.invoke(app, ["exercises", "list", "--show-timestamp"])
    assert result.exit_code == 0
    assert "last submitted: 2026-07-21T15:26:27.257941Z" in result.output
    assert "last submitted: -" in result.output


def test_list_unsolved_flag_shows_pending_and_failed_but_not_success(logged_in_with_classroom, mock_exercises):
    result = runner.invoke(app, ["exercises", "list", "--unsolved"])
    assert result.exit_code == 0
    assert "sum-two-numbers" in result.output
    assert "broken-attempt" in result.output
    assert "hello-world" not in result.output


def test_list_unsolved_flag_with_nothing_unsolved(logged_in_with_classroom, monkeypatch):
    monkeypatch.setattr(ApiClient, "list_exercises", lambda self: [FAKE_EXERCISES[0]])
    result = runner.invoke(app, ["exercises", "list", "--unsolved"])
    assert result.exit_code == 0
    assert "No exercises available." in result.output
