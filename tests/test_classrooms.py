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


def test_switch_with_valid_slug_clears_active_practice(logged_in, mock_classrooms):
    logged_in.set_active_practice("some-practice")
    result = runner.invoke(app, ["switch", "turma-b"])
    assert result.exit_code == 0
    assert logged_in.get_active_practice() is None


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


# --- interactive menu (no slug, in a terminal) ---

INTERACTIVE_PRACTICES = [
    {"slug": "lista-1", "title": "Lista 1", "is_timed": False, "duration_minutes": None, "window_status": "open", "attempt": None},
]


@pytest.fixture
def interactive(monkeypatch):
    """Pretends to be in a terminal; records menus and answers them from a queue."""
    from eliude_cli import prompts

    state = {"answers": [], "menus": []}

    def fake_select(message, options, default=None):
        state["menus"].append({"message": message, "options": options, "default": default})
        return state["answers"].pop(0)

    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "select", fake_select)
    return state


@pytest.fixture
def mock_practice_api(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: INTERACTIVE_PRACTICES)
    monkeypatch.setattr(ApiClient, "start_practice", lambda self, slug: {"attempt": None})


def test_interactive_switch_picks_classroom_then_practice(logged_in, mock_classrooms, mock_practice_api, interactive):
    interactive["answers"] = ["turma-b", "lista-1"]
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0, result.output
    assert [m["message"] for m in interactive["menus"]] == ["Choose a classroom:", "Choose a practice:"]
    assert [o.value for o in interactive["menus"][0]["options"]] == ["turma-a", "turma-b"]
    assert logged_in.get_active_classroom() == "turma-b"
    assert logged_in.get_active_practice() == "lista-1"
    assert "Switched to classroom 'Turma B' (turma-b)." in result.output
    assert "Using practice 'Lista 1' (lista-1)." in result.output


def test_interactive_switch_highlights_the_active_classroom(logged_in, mock_classrooms, mock_practice_api, interactive):
    logged_in.set_active_classroom("turma-b")
    interactive["answers"] = ["turma-b", "lista-1"]
    runner.invoke(app, ["switch"])
    menu = interactive["menus"][0]
    assert menu["default"] == "turma-b"
    assert [o.label for o in menu["options"]] == ["Turma A", "Turma B (current)"]


def test_interactive_switch_shows_the_classroom_menu_even_with_a_single_classroom(logged_in, monkeypatch, mock_practice_api, interactive):
    monkeypatch.setattr(ApiClient, "list_classrooms", lambda self: FAKE_CLASSROOMS[:1])
    interactive["answers"] = ["turma-a", "lista-1"]
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 0, result.output
    assert [m["message"] for m in interactive["menus"]] == ["Choose a classroom:", "Choose a practice:"]
    assert logged_in.get_active_classroom() == "turma-a"
    assert logged_in.get_active_practice() == "lista-1"


def test_interactive_switch_cancelled_at_classroom_changes_nothing(logged_in, mock_classrooms, mock_practice_api, interactive):
    logged_in.set_active_classroom("turma-a")
    logged_in.set_active_practice("antiga")
    interactive["answers"] = [None]
    result = runner.invoke(app, ["switch"])
    assert result.exit_code == 1
    assert "Cancelled." in result.output
    assert logged_in.get_active_classroom() == "turma-a"
    assert logged_in.get_active_practice() == "antiga"


def test_switch_with_slug_skips_the_classroom_menu_but_opens_the_practice_menu(logged_in, mock_classrooms, mock_practice_api, interactive):
    interactive["answers"] = ["lista-1"]
    result = runner.invoke(app, ["switch", "turma-b"])
    assert result.exit_code == 0, result.output
    assert [m["message"] for m in interactive["menus"]] == ["Choose a practice:"]
    assert logged_in.get_active_classroom() == "turma-b"
    assert logged_in.get_active_practice() == "lista-1"
