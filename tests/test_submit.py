import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_RESULT = {
    "status": "passed",
    "result_detail": {"test_cases": [{"passed": True}], "passed_count": 1, "total_count": 1},
}


PLAIN_QUESTION = {"required_files": ["main.c"], "extra_file_patterns": [], "files": []}

PROJECT_QUESTION = {
    "required_files": ["src/pilha.c"],
    "extra_file_patterns": ["src/*.c", "include/*.h"],
    "files": [
        {"path": "src/pilha.c", "kind": "student", "content": "/* aqui */"},
        {"path": "include/pilha.h", "kind": "provided", "content": "void empilha(int);"},
    ],
}


@pytest.fixture
def logged_in_with_practice(cli_config, monkeypatch):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    cli_config.set_active_practice("turma-a-exercicios")
    monkeypatch.setattr(ApiClient, "get_question", lambda self, slug: PLAIN_QUESTION)
    return cli_config


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(ApiClient, "submit", lambda self, slug, files: calls.append(files) or FAKE_RESULT)
    return calls


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
    assert "Result: 1/1 test cases passed, but criteria not met" in result.output


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
    assert "Result: 1/1 test cases passed" in result.output
    assert "but criteria not met" not in result.output


def test_single_file_goes_as_main_c_whatever_its_name(logged_in_with_practice, source_file, sent):
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 0
    assert sent == [{"main.c": "int main(void) { return 0; }"}]


def _project(tmp_path):
    root = tmp_path / "q1"
    (root / "src").mkdir(parents=True)
    (root / "include").mkdir()
    (root / ".git").mkdir()
    (root / "src" / "pilha.c").write_text("int topo;")
    (root / "src" / "util.c").write_text("int u;")
    (root / "src" / "pilha.o").write_text("binario")
    (root / "include" / "pilha.h").write_text("provided, not sent")
    (root / ".git" / "config.c").write_text("hidden")
    (root / "notas.txt").write_text("not expected")
    return root


def test_project_folder_sends_only_expected_files(logged_in_with_practice, tmp_path, monkeypatch, sent):
    monkeypatch.setattr(ApiClient, "get_question", lambda self, slug: PROJECT_QUESTION)
    root = _project(tmp_path)
    result = runner.invoke(app, ["submit", "q1", str(root)])
    assert result.exit_code == 0, result.output
    assert sent == [{"src/pilha.c": "int topo;", "src/util.c": "int u;"}]
    assert "src/util.c" in result.output


def test_project_defaults_to_the_slug_folder(logged_in_with_practice, tmp_path, monkeypatch, sent):
    monkeypatch.setattr(ApiClient, "get_question", lambda self, slug: PROJECT_QUESTION)
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["submit", "q1"])
    assert result.exit_code == 0, result.output
    assert list(sent[0]) == ["src/pilha.c", "src/util.c"]


def test_without_path_or_folder_explains_what_to_do(logged_in_with_practice, tmp_path, monkeypatch, sent):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["submit", "q1"])
    assert result.exit_code == 1
    assert "./q1/" in result.output
    assert sent == []


def test_project_reports_missing_required_files(logged_in_with_practice, tmp_path, monkeypatch, sent):
    monkeypatch.setattr(ApiClient, "get_question", lambda self, slug: PROJECT_QUESTION)
    root = tmp_path / "q1"
    root.mkdir()
    result = runner.invoke(app, ["submit", "q1", str(root)])
    assert result.exit_code == 1
    assert "src/pilha.c" in result.output
    assert sent == []


def test_single_file_is_refused_for_a_project(logged_in_with_practice, source_file, monkeypatch, sent):
    monkeypatch.setattr(ApiClient, "get_question", lambda self, slug: PROJECT_QUESTION)
    result = runner.invoke(app, ["submit", "q1", str(source_file)])
    assert result.exit_code == 1
    assert "src/pilha.c" in result.output
    assert sent == []
