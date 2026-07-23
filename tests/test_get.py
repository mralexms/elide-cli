import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_SUBMISSION = {"source_code": "int main(void) { return 0; }\n"}


@pytest.fixture
def logged_in_with_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    cli_config.set_active_practice("turma-a-exercicios")
    return cli_config


@pytest.fixture
def mock_latest_submission(monkeypatch):
    monkeypatch.setattr(ApiClient, "get_latest_submission", lambda self, slug: FAKE_SUBMISSION)


def test_get_requires_login(cli_config):
    result = runner.invoke(app, ["get", "hello-world"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_get_without_save_prints_to_stdout(logged_in_with_classroom, mock_latest_submission, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["get", "hello-world"])
    assert result.exit_code == 0
    assert FAKE_SUBMISSION["source_code"] in result.output
    assert not (tmp_path / "hello-world.c").exists()


def test_get_save_writes_file_named_after_slug(logged_in_with_classroom, mock_latest_submission, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["get", "hello-world", "--save"])
    assert result.exit_code == 0
    saved = tmp_path / "hello-world.c"
    assert saved.exists()
    assert saved.read_text() == FAKE_SUBMISSION["source_code"]


def test_get_save_overwrite_flag_skips_prompt(logged_in_with_classroom, mock_latest_submission, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "hello-world.c"
    existing.write_text("old content")
    result = runner.invoke(app, ["get", "hello-world", "--save", "--overwrite"])
    assert result.exit_code == 0
    assert existing.read_text() == FAKE_SUBMISSION["source_code"]


def test_get_save_prompts_and_overwrites_on_confirm(logged_in_with_classroom, mock_latest_submission, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "hello-world.c"
    existing.write_text("old content")
    result = runner.invoke(app, ["get", "hello-world", "--save"], input="y\n")
    assert result.exit_code == 0
    assert "already exists" in result.output
    assert existing.read_text() == FAKE_SUBMISSION["source_code"]


def test_get_save_prompts_and_saves_under_new_name_on_decline(
    logged_in_with_classroom, mock_latest_submission, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "hello-world.c"
    existing.write_text("old content")
    result = runner.invoke(app, ["get", "hello-world", "--save"], input="n\nrenamed.c\n")
    assert result.exit_code == 0
    assert existing.read_text() == "old content"
    assert (tmp_path / "renamed.c").read_text() == FAKE_SUBMISSION["source_code"]
