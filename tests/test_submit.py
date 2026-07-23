import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_RESULT = {
    "status": "passed",
    "result_detail": {"test_cases": [{"passed": True}], "passed_count": 1, "total_count": 1},
}


@pytest.fixture
def logged_in_with_practice(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    cli_config.set_active_practice("turma-a-exercicios")
    return cli_config


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "solucao.c"
    path.write_text("int main(void) { return 0; }")
    return path


def test_submit_requires_login(cli_config, source_file):
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_submit_requires_active_practice(cli_config, source_file):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 1
    assert "No active practice set" in result.output


def test_submit_passing_solution_exits_zero(logged_in_with_practice, source_file, monkeypatch):
    monkeypatch.setattr(ApiClient, "submit", lambda self, slug, source_code: FAKE_RESULT)
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 0
    assert "PASS" in result.output


def test_submit_failing_solution_exits_nonzero(logged_in_with_practice, source_file, monkeypatch):
    failed = {**FAKE_RESULT, "status": "failed", "result_detail": {"test_cases": [{"passed": False}], "passed_count": 0, "total_count": 1}}
    monkeypatch.setattr(ApiClient, "submit", lambda self, slug, source_code: failed)
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 1


def test_submit_shows_ai_criteria_not_met(logged_in_with_practice, source_file, monkeypatch):
    failed = {
        "status": "failed",
        "result_detail": {
            "test_cases": [{"passed": True}],
            "passed_count": 1,
            "total_count": 1,
            "ai_check": {"criteria_met": False, "feedback": "Uses a while loop instead of a for loop."},
        },
    }
    monkeypatch.setattr(ApiClient, "submit", lambda self, slug, source_code: failed)
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 1
    assert "Criteria not met" in result.output
    assert "Uses a while loop instead of a for loop." in result.output


def test_submit_hides_criteria_message_when_met(logged_in_with_practice, source_file, monkeypatch):
    passed = {
        **FAKE_RESULT,
        "result_detail": {
            **FAKE_RESULT["result_detail"],
            "ai_check": {"criteria_met": True, "feedback": "Uses a for loop."},
        },
    }
    monkeypatch.setattr(ApiClient, "submit", lambda self, slug, source_code: passed)
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 0
    assert "Criteria not met" not in result.output
