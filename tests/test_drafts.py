from pathlib import Path

import pytest
from typer.testing import CliRunner

from eliude_cli import editor
from eliude_cli.client import ApiClient, ApiError
from eliude_cli.main import app

runner = CliRunner()

PLAIN_QUESTION = {"required_files": ["main.c"], "extra_file_patterns": [], "files": []}

PROJECT_QUESTION = {
    "required_files": ["src/pilha.c"],
    "extra_file_patterns": ["src/*.c"],
    "files": [
        {"path": "src/pilha.c", "kind": "student", "content": "/* comece aqui */\n"},
        {"path": "include/pilha.h", "kind": "provided", "content": "void empilha(int);\n"},
    ],
}

DRAFT = {"version": 3, "updated_at": "2026-11-12T14:32:00-03:00", "files": [{"path": "main.c", "content": "/* rascunho */\n"}]}
SUBMISSION = {"created_at": "2026-11-12T10:00:00-03:00", "files": [{"path": "main.c", "content": "/* envio */\n"}]}


class Backend:
    """The API calls `save`/`load` make, recorded."""

    def __init__(self, monkeypatch, question=PLAIN_QUESTION, draft=None, submission=None, finished=False):
        self.question, self.draft, self.submission = question, draft, submission
        self.saves = []
        self.save_error = None
        backend = self

        def get_latest_submission(client, slug):
            if backend.submission is None:
                raise ApiError("Not found.", status=404)
            return backend.submission

        def save_draft(client, slug, files, base_version=None):
            backend.saves.append({"files": files, "base_version": base_version})
            error, backend.save_error = backend.save_error, None
            if error:
                raise error
            return {"version": 9}

        practices = [{"slug": "lista-1", "title": "Lista 1", "window_status": "closed" if finished else "open"}]
        monkeypatch.setattr(ApiClient, "get_question", lambda client, slug: backend.question)
        monkeypatch.setattr(ApiClient, "get_draft", lambda client, slug: backend.draft)
        monkeypatch.setattr(ApiClient, "get_latest_submission", get_latest_submission)
        monkeypatch.setattr(ApiClient, "save_draft", save_draft)
        monkeypatch.setattr(ApiClient, "list_practices", lambda client: practices)


class FakeEditor:
    """Stands in for the editor: records what it was asked to open and
    applies `change` to those files, as if the student typed and saved."""

    def __init__(self, monkeypatch, change=None, ok=True):
        self.opened = []
        self.change, self.ok = change, ok
        monkeypatch.setattr(editor, "edit", self)

    def __call__(self, paths):
        self.opened.append(list(paths))
        self.folder = paths[0].parent
        if self.change:
            self.change(paths)
        return self.ok


@pytest.fixture
def logged_in(cli_config, monkeypatch, tmp_path):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    cli_config.set_active_practice("lista-1")
    temp = tmp_path / "temp"
    temp.mkdir()
    monkeypatch.setattr("tempfile.tempdir", str(temp))
    return cli_config


def append(text):
    def change(paths):
        with open(paths[0], "a", encoding="utf-8") as f:
            f.write(text)

    return change


# --- eliude save ---


def test_save_sends_a_file_without_grading(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch)
    monkeypatch.setattr(ApiClient, "submit", lambda *a: pytest.fail("save must not grade"))
    source = tmp_path / "q1.c"
    source.write_text("int main(void) { return 0; }\n")
    result = runner.invoke(app, ["save", "q1", str(source)])
    assert result.exit_code == 0, result.output
    assert backend.saves == [{"files": {"main.c": "int main(void) { return 0; }\n"}, "base_version": None}]
    assert "not graded" in result.output


def test_save_without_a_path_reads_the_question_folder(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch, question=PROJECT_QUESTION)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "q1" / "src").mkdir(parents=True)
    (tmp_path / "q1" / "include").mkdir()
    (tmp_path / "q1" / "src" / "pilha.c").write_text("/* pilha */\n")
    (tmp_path / "q1" / "include" / "pilha.h").write_text("/* do professor */\n")
    result = runner.invoke(app, ["save", "q1"])
    assert result.exit_code == 0, result.output
    assert backend.saves[0]["files"] == {"src/pilha.c": "/* pilha */\n"}


def test_save_shows_the_servers_refusal(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch)
    backend.save_error = ApiError("This practice has finished and no longer accepts submissions.", 403, "practice_finished")
    source = tmp_path / "q1.c"
    source.write_text("x")
    result = runner.invoke(app, ["save", "q1", str(source)])
    assert result.exit_code == 1
    assert "no longer accepts submissions" in result.output


# --- eliude load ---


def test_load_opens_the_draft_when_it_is_newer_and_saves_the_change(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT, submission=SUBMISSION)
    fake = FakeEditor(monkeypatch, change=append("int main(void) { return 0; }\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 0, result.output
    assert "saved code from 11/12" in result.output
    assert [p.name for p in fake.opened[0]] == ["main.c"]
    assert backend.saves == [
        {"files": {"main.c": "/* rascunho */\nint main(void) { return 0; }\n"}, "base_version": 3}
    ]
    assert "eliude submit q1 --draft" in result.output
    assert not fake.folder.exists()  # saved: the temporary folder goes away


def test_load_prefers_a_submission_newer_than_the_draft(logged_in, monkeypatch):
    newer = dict(SUBMISSION, created_at="2026-11-12T15:00:00-03:00")
    backend = Backend(monkeypatch, draft=DRAFT, submission=newer)
    FakeEditor(monkeypatch, change=append("// mais\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert "latest submission" in result.output
    # Still checked against the draft's version, so a save elsewhere isn't lost.
    assert backend.saves[0] == {"files": {"main.c": "/* envio */\n// mais\n"}, "base_version": 3}


def test_load_without_anything_saved_opens_the_starting_files(logged_in, monkeypatch):
    backend = Backend(monkeypatch, question=PROJECT_QUESTION)
    fake = FakeEditor(monkeypatch, change=append("void empilha(int x) {}\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 0, result.output
    assert "starting files" in result.output
    # Only the student's file is opened; the teacher's is there to read.
    [opened] = fake.opened[0]
    assert opened.as_posix().endswith("/src/pilha.c")
    assert backend.saves == [
        {"files": {"src/pilha.c": "/* comece aqui */\nvoid empilha(int x) {}\n"}, "base_version": 0}
    ]


def test_load_project_keeps_the_teachers_files_out_of_the_save(logged_in, monkeypatch):
    backend = Backend(monkeypatch, question=PROJECT_QUESTION)

    def change(paths):
        folder = paths[0].parents[1]
        assert (folder / "include" / "pilha.h").read_text() == "void empilha(int);\n"
        (folder / "include" / "pilha.h").write_text("/* mexido */\n")
        (folder / "src" / "extra.c").write_text("/* novo */\n")

    FakeEditor(monkeypatch, change=change)
    runner.invoke(app, ["load", "q1"])
    assert backend.saves[0]["files"] == {"src/extra.c": "/* novo */\n", "src/pilha.c": "/* comece aqui */\n"}


def test_load_without_changes_saves_nothing(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT)
    fake = FakeEditor(monkeypatch)
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 0
    assert backend.saves == []
    assert "No changes" in result.output
    assert not fake.folder.exists()


def test_a_failed_save_keeps_the_files_and_says_how_to_retry(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT)
    backend.save_error = ApiError("Could not reach the Eliude server at http://x.")
    fake = FakeEditor(monkeypatch, change=append("// importante\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    kept = fake.folder / "main.c"
    assert kept.read_text() == "/* rascunho */\n// importante\n"
    assert f"eliude save q1 {kept}" in result.output.replace("\n", "")


def test_an_editor_error_saves_nothing_but_keeps_the_files(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT)
    fake = FakeEditor(monkeypatch, change=append("// :cq\n"), ok=False)
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    assert backend.saves == []
    assert "exited with an error" in result.output
    assert fake.folder.exists()


def test_a_finished_practice_opens_but_does_not_save(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT, finished=True)
    fake = FakeEditor(monkeypatch, change=append("// tarde\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    assert "changes won't be saved" in result.output
    assert "eliude save" not in result.output  # the server would refuse it too
    assert backend.saves == []
    assert fake.folder.exists()


def test_a_conflict_without_a_terminal_says_why_and_keeps_the_files(logged_in, monkeypatch):
    backend = Backend(monkeypatch, draft=DRAFT)
    backend.save_error = ApiError("saved somewhere else", 409, "draft_conflict", {"version": 4})
    fake = FakeEditor(monkeypatch, change=append("// meu\n"))
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    assert "yours wasn't sent" in result.output
    assert len(backend.saves) == 1
    assert fake.folder.exists()


def test_a_conflict_asks_before_overwriting(logged_in, monkeypatch):
    from eliude_cli import prompts

    backend = Backend(monkeypatch, draft=DRAFT)
    backend.save_error = ApiError("saved somewhere else", 409, "draft_conflict", {"version": 4})
    FakeEditor(monkeypatch, change=append("// meu\n"))
    asked = []
    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "confirm", lambda message, default=False: asked.append(message) or True)
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 0, result.output
    assert "somewhere else" in asked[0]
    assert [save["base_version"] for save in backend.saves] == [3, None]


def test_a_declined_conflict_keeps_the_files(logged_in, monkeypatch):
    from eliude_cli import prompts

    backend = Backend(monkeypatch, draft=DRAFT)
    backend.save_error = ApiError("saved somewhere else", 409, "draft_conflict", {"version": 4})
    fake = FakeEditor(monkeypatch, change=append("// meu\n"))
    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "confirm", lambda message, default=False: False)
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    assert len(backend.saves) == 1
    assert fake.folder.exists()


def test_load_without_an_editor_explains(logged_in, monkeypatch):
    Backend(monkeypatch, draft=DRAFT)

    def no_editor(paths):
        raise editor.EditorError("no editor")

    monkeypatch.setattr(editor, "edit", no_editor)
    result = runner.invoke(app, ["load", "q1"])
    assert result.exit_code == 1
    assert "EDITOR" in result.output


# --- submit --draft and get --draft ---


def test_submit_draft_grades_the_saved_code(logged_in, monkeypatch):
    Backend(monkeypatch, draft=DRAFT)
    sent = []
    result_ok = {"status": "passed", "result_detail": {"test_cases": [{"passed": True}], "passed_count": 1, "total_count": 1}}
    monkeypatch.setattr(ApiClient, "submit", lambda client, slug, files: sent.append(files) or result_ok)
    result = runner.invoke(app, ["submit", "q1", "--draft"])
    assert result.exit_code == 0, result.output
    assert sent == [{"main.c": "/* rascunho */\n"}]


def test_submit_draft_without_a_draft_explains(logged_in, monkeypatch):
    Backend(monkeypatch)
    result = runner.invoke(app, ["submit", "q1", "--draft"])
    assert result.exit_code == 1
    assert "Nothing saved for 'q1'" in result.output


def test_submit_refuses_draft_and_path_together(logged_in, monkeypatch, tmp_path):
    source = tmp_path / "q1.c"
    source.write_text("x")
    result = runner.invoke(app, ["submit", "q1", str(source), "--draft"])
    assert result.exit_code == 1
    assert "not both" in result.output


def test_get_draft_prints_the_saved_code(logged_in, monkeypatch):
    Backend(monkeypatch, draft=DRAFT, submission=SUBMISSION)
    result = runner.invoke(app, ["get", "q1", "--draft"])
    assert result.exit_code == 0
    assert "/* rascunho */" in result.output
    assert "/* envio */" not in result.output


def test_get_draft_without_a_draft_explains(logged_in, monkeypatch):
    Backend(monkeypatch)
    result = runner.invoke(app, ["get", "q1", "--draft"])
    assert result.exit_code == 1
    assert "Nothing saved" in result.output


# --- the editor ---


@pytest.fixture
def clean_editor_env(monkeypatch):
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.setattr(editor.sys, "platform", "darwin")


def test_visual_wins_over_editor(clean_editor_env, monkeypatch):
    monkeypatch.setenv("EDITOR", "nano")
    monkeypatch.setenv("VISUAL", "code --wait")
    assert editor.command() == ["code", "--wait"]


def test_falls_back_to_the_first_editor_installed(clean_editor_env, monkeypatch):
    monkeypatch.setattr(editor.shutil, "which", lambda name: "/usr/bin/vi" if name == "vi" else None)
    assert editor.command() == ["vi"]


def test_no_editor_at_all(clean_editor_env, monkeypatch):
    monkeypatch.setattr(editor.shutil, "which", lambda name: None)
    assert editor.command() is None
    with pytest.raises(editor.EditorError):
        editor.edit([Path("main.c")])


def test_editor_exit_code_decides(clean_editor_env, monkeypatch):
    monkeypatch.setenv("EDITOR", "vim")
    calls = []

    class Done:
        def __init__(self, code):
            self.returncode = code

    monkeypatch.setattr(editor.subprocess, "run", lambda cmd: calls.append(cmd) or Done(0))
    assert editor.edit([Path("a.c"), Path("b.c")]) is True
    assert calls == [["vim", "a.c", "b.c"]]
    monkeypatch.setattr(editor.subprocess, "run", lambda cmd: Done(1))
    assert editor.edit([Path("a.c")]) is False


def test_notepad_opens_one_file_at_a_time(clean_editor_env, monkeypatch):
    monkeypatch.setattr(editor.sys, "platform", "win32")
    calls = []

    class Done:
        returncode = 0

    monkeypatch.setattr(editor.subprocess, "run", lambda cmd: calls.append(cmd) or Done())
    editor.edit([Path("a.c"), Path("b.c")])
    assert calls == [["notepad", "a.c"], ["notepad", "b.c"]]


# --- eliude load <questão> <arquivo> ---


def test_load_into_a_new_local_file_keeps_it(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch, draft=DRAFT)
    fake = FakeEditor(monkeypatch, change=append("// local\n"))
    target = tmp_path / "q1.c"
    result = runner.invoke(app, ["load", "q1", str(target)])
    assert result.exit_code == 0, result.output
    assert fake.opened == [[target]]
    assert target.read_text() == "/* rascunho */\n// local\n"  # stays, unlike the temporary folder
    assert backend.saves == [{"files": {"main.c": "/* rascunho */\n// local\n"}, "base_version": 3}]
    assert f"Written to {target}" in result.output.replace("\n", "")


def test_load_into_an_identical_file_does_not_ask(logged_in, monkeypatch, tmp_path):
    Backend(monkeypatch, draft=DRAFT)
    FakeEditor(monkeypatch)
    target = tmp_path / "q1.c"
    target.write_text("/* rascunho */\n")
    result = runner.invoke(app, ["load", "q1", str(target)])
    assert result.exit_code == 0, result.output
    assert "No changes" in result.output


def test_load_asks_before_replacing_a_different_local_file(logged_in, monkeypatch, tmp_path):
    from eliude_cli import prompts

    Backend(monkeypatch, draft=DRAFT)
    fake = FakeEditor(monkeypatch)
    target = tmp_path / "q1.c"
    target.write_text("/* meu trabalho local */\n")
    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "confirm", lambda message, default=False: False)
    result = runner.invoke(app, ["load", "q1", str(target)])
    assert result.exit_code == 1
    assert target.read_text() == "/* meu trabalho local */\n"
    assert fake.opened == []


def test_load_refuses_to_replace_without_a_terminal_unless_overwrite(logged_in, monkeypatch, tmp_path):
    Backend(monkeypatch, draft=DRAFT)
    FakeEditor(monkeypatch)
    target = tmp_path / "q1.c"
    target.write_text("/* meu trabalho local */\n")
    refused = runner.invoke(app, ["load", "q1", str(target)])
    assert refused.exit_code == 1
    assert "--overwrite" in refused.output
    assert target.read_text() == "/* meu trabalho local */\n"
    replaced = runner.invoke(app, ["load", "q1", str(target), "--overwrite"])
    assert replaced.exit_code == 0, replaced.output
    assert target.read_text() == "/* rascunho */\n"


def test_load_a_project_into_a_folder(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch, question=PROJECT_QUESTION)
    fake = FakeEditor(monkeypatch, change=append("void empilha(int x) {}\n"))
    folder = tmp_path / "q1"
    result = runner.invoke(app, ["load", "q1", str(folder)])
    assert result.exit_code == 0, result.output
    assert fake.opened == [[folder / "src" / "pilha.c"]]
    assert (folder / "include" / "pilha.h").read_text() == "void empilha(int);\n"
    assert backend.saves[0]["files"] == {"src/pilha.c": "/* comece aqui */\nvoid empilha(int x) {}\n"}


def test_load_a_project_into_a_file_is_refused(logged_in, monkeypatch, tmp_path):
    Backend(monkeypatch, question=PROJECT_QUESTION)
    FakeEditor(monkeypatch)
    target = tmp_path / "q1.c"
    target.write_text("x")
    result = runner.invoke(app, ["load", "q1", str(target)])
    assert result.exit_code == 1
    assert "project folder" in result.output


def test_a_failed_save_from_a_local_file_points_at_it(logged_in, monkeypatch, tmp_path):
    backend = Backend(monkeypatch, draft=DRAFT)
    backend.save_error = ApiError("Could not reach the Eliude server at http://x.")
    FakeEditor(monkeypatch, change=append("// importante\n"))
    target = tmp_path / "q1.c"
    result = runner.invoke(app, ["load", "q1", str(target)])
    assert result.exit_code == 1
    assert target.read_text() == "/* rascunho */\n// importante\n"
    assert f"eliude save q1 {target}" in result.output.replace("\n", "")
