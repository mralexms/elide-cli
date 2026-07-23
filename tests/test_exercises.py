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
        "tags": [],
    },
    {
        "slug": "sum-two-numbers",
        "title": "Sum Two Numbers",
        "difficulty": "easy",
        "status": "pending",
        "last_submission_at": None,
        "tags": [{"name": "Vetores", "slug": "vetores"}],
    },
    {
        "slug": "broken-attempt",
        "title": "Broken Attempt",
        "difficulty": "easy",
        "status": "failure",
        "last_submission_at": "2026-07-21T16:00:00.000000Z",
        "tags": [],
    },
]


@pytest.fixture
def logged_in_with_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    return cli_config


@pytest.fixture
def mock_exercises(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_exercises", lambda self, tag=None: FAKE_EXERCISES)


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


def test_exercises_bare_invocation_matches_list(logged_in_with_classroom, mock_exercises):
    bare = runner.invoke(app, ["exercises"])
    full = runner.invoke(app, ["exercises", "list"])
    assert bare.exit_code == 0
    assert bare.output == full.output


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
    monkeypatch.setattr(ApiClient, "list_exercises", lambda self, tag=None: [FAKE_EXERCISES[0]])
    result = runner.invoke(app, ["exercises", "list", "--unsolved"])
    assert result.exit_code == 0
    assert "No exercises available." in result.output


def test_list_shows_tags_inline(logged_in_with_classroom, mock_exercises):
    result = runner.invoke(app, ["exercises", "list"])
    assert result.exit_code == 0
    assert "Vetores" in result.output


def test_list_tag_option_forwards_to_client(logged_in_with_classroom, monkeypatch):
    captured = {}

    def fake_list_exercises(self, tag=None):
        captured["tag"] = tag
        return FAKE_EXERCISES

    monkeypatch.setattr(ApiClient, "list_exercises", fake_list_exercises)
    result = runner.invoke(app, ["exercises", "list", "--tag", "vetores"])
    assert result.exit_code == 0
    assert captured["tag"] == "vetores"


FAKE_EXERCISE_DETAIL = {
    "title": "Hello World",
    "difficulty": "easy",
    "time_limit_seconds": 5,
    "memory_limit_mb": 64,
    "statement": "Say hello.",
    "tags": [{"name": "Loops", "slug": "loops"}],
    "sample_test_cases": [
        {"id": 1, "stdin_data": "World\n", "expected_stdout": "Hello, World!\n", "order": 1},
    ],
}

FAKE_EXERCISE_DETAIL_NO_SAMPLES = {**FAKE_EXERCISE_DETAIL, "sample_test_cases": []}


@pytest.fixture
def mock_exercise_detail(monkeypatch):
    monkeypatch.setattr(ApiClient, "get_exercise", lambda self, slug: FAKE_EXERCISE_DETAIL)


def test_show_requires_login(cli_config):
    result = runner.invoke(app, ["exercises", "show", "hello-world"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_show_displays_tags(logged_in_with_classroom, mock_exercise_detail):
    result = runner.invoke(app, ["exercises", "show", "hello-world"])
    assert result.exit_code == 0
    assert "Tags: Loops" in result.output


def test_show_shortcut_matches_exercises_show(logged_in_with_classroom, mock_exercise_detail):
    shortcut = runner.invoke(app, ["show", "hello-world"])
    full = runner.invoke(app, ["exercises", "show", "hello-world"])
    assert shortcut.exit_code == 0
    assert shortcut.output == full.output


def test_show_without_download_does_not_write_files(logged_in_with_classroom, mock_exercise_detail, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["exercises", "show", "hello-world"])
    assert result.exit_code == 0
    assert not (tmp_path / "hello-world_input.txt").exists()


def test_show_download_saves_first_sample_test_case(logged_in_with_classroom, mock_exercise_detail, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["exercises", "show", "hello-world", "--download"])
    assert result.exit_code == 0
    assert (tmp_path / "hello-world_input.txt").read_text() == "World\n"
    assert (tmp_path / "hello-world_output.txt").read_text() == "Hello, World!\n"


def test_show_download_with_no_sample_test_cases(logged_in_with_classroom, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ApiClient, "get_exercise", lambda self, slug: FAKE_EXERCISE_DETAIL_NO_SAMPLES)
    result = runner.invoke(app, ["exercises", "show", "hello-world", "--download"])
    assert result.exit_code == 0
    assert "No sample test case available" in result.output
    assert not (tmp_path / "hello-world_input.txt").exists()
