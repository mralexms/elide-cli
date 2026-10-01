import pytest
from typer.testing import CliRunner

from eliude_cli.client import ApiClient
from eliude_cli.main import app

runner = CliRunner()

FAKE_PRACTICES = [
    {
        "slug": "turma-a-exercicios",
        "title": "Exercícios",
        "is_timed": False,
        "duration_minutes": None,
        "window_status": "open",
        "attempt": None,
    },
    {
        "slug": "prova-1",
        "title": "Prova 1",
        "is_timed": True,
        "duration_minutes": 60,
        "window_status": "open",
        "attempt": None,
    },
]


@pytest.fixture
def logged_in_with_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    cli_config.set_active_classroom("turma-a")
    return cli_config


@pytest.fixture
def mock_practices(monkeypatch):
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: FAKE_PRACTICES)


def test_practices_list_requires_login(cli_config):
    result = runner.invoke(app, ["practices", "list"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_practices_list_requires_active_classroom(cli_config):
    cli_config.set_token("faketoken123", "alice")
    result = runner.invoke(app, ["practices", "list"])
    assert result.exit_code == 1
    assert "No active classroom set" in result.output


def test_practices_list_shows_all_practices(logged_in_with_classroom, mock_practices):
    result = runner.invoke(app, ["practices", "list"])
    assert result.exit_code == 0
    assert "turma-a-exercicios" in result.output
    assert "prova-1" in result.output
    assert "no time limit" in result.output
    assert "timed 60min" in result.output


def test_practices_bare_invocation_matches_list(logged_in_with_classroom, mock_practices):
    bare = runner.invoke(app, ["practices"])
    full = runner.invoke(app, ["practices", "list"])
    assert bare.exit_code == 0
    assert bare.output == full.output


def test_switch_no_arg_lists_same_as_practices_list(logged_in_with_classroom, mock_practices):
    switch_result = runner.invoke(app, ["practices", "switch"])
    list_result = runner.invoke(app, ["practices", "list"])
    assert switch_result.exit_code == 0
    assert switch_result.output == list_result.output


def test_switch_to_untimed_practice_sets_active_with_no_deadline(logged_in_with_classroom, mock_practices, monkeypatch):
    monkeypatch.setattr(ApiClient, "start_practice", lambda self, slug: {"attempt": None, "title": "Exercícios"})
    result = runner.invoke(app, ["practices", "switch", "turma-a-exercicios"])
    assert result.exit_code == 0
    assert "Using practice 'Exercícios' (turma-a-exercicios)." in result.output
    assert "Time limit" not in result.output
    assert logged_in_with_classroom.get_active_practice() == "turma-a-exercicios"


def test_switch_to_timed_practice_shows_deadline(logged_in_with_classroom, mock_practices, monkeypatch):
    monkeypatch.setattr(
        ApiClient,
        "start_practice",
        lambda self, slug: {"attempt": {"started_at": "2026-07-23T10:00:00Z", "ends_at": "2026-07-23T11:00:00Z"}, "title": "Prova 1"},
    )
    result = runner.invoke(app, ["practices", "switch", "prova-1"])
    assert result.exit_code == 0
    assert "Time limit: ends at 2026-07-23T11:00:00Z" in result.output
    assert logged_in_with_classroom.get_active_practice() == "prova-1"


def test_switch_with_invalid_slug_fails_without_changing_config(logged_in_with_classroom, mock_practices):
    logged_in_with_classroom.set_active_practice("turma-a-exercicios")
    result = runner.invoke(app, ["practices", "switch", "does-not-exist"])
    assert result.exit_code == 1
    assert "No practice 'does-not-exist'" in result.output
    assert logged_in_with_classroom.get_active_practice() == "turma-a-exercicios"


def test_practices_list_with_none_available(logged_in_with_classroom, monkeypatch):
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: [])
    result = runner.invoke(app, ["practices", "list"])
    assert result.exit_code == 1
    assert "no practices yet" in result.output


# --- interactive menu (no slug, in a terminal) ---


@pytest.fixture
def interactive(monkeypatch):
    """Pretends to be in a terminal; records menus/confirms and answers them from queues."""
    from eliude_cli import prompts

    state = {"answers": [], "menus": [], "confirm_answers": [], "confirms": []}

    def fake_select(message, options, default=None):
        state["menus"].append({"message": message, "options": options, "default": default})
        return state["answers"].pop(0)

    def fake_confirm(message):
        state["confirms"].append(message)
        return state["confirm_answers"].pop(0)

    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "select", fake_select)
    monkeypatch.setattr(prompts, "confirm", fake_confirm)
    return state


@pytest.fixture
def started(monkeypatch):
    calls = []

    def fake_start(self, slug):
        calls.append(slug)
        return {"attempt": None}

    monkeypatch.setattr(ApiClient, "start_practice", fake_start)
    return calls


def test_interactive_practice_switch_activates_the_chosen_practice(logged_in_with_classroom, mock_practices, started, interactive):
    interactive["answers"] = ["turma-a-exercicios"]
    result = runner.invoke(app, ["practices", "switch"])
    assert result.exit_code == 0, result.output
    assert started == ["turma-a-exercicios"]
    assert interactive["confirms"] == []
    assert logged_in_with_classroom.get_active_practice() == "turma-a-exercicios"


def test_interactive_timed_practice_asks_before_starting_the_clock(logged_in_with_classroom, mock_practices, started, interactive):
    interactive["answers"] = ["prova-1"]
    interactive["confirm_answers"] = [True]
    result = runner.invoke(app, ["practices", "switch"])
    assert result.exit_code == 0, result.output
    assert "clock starts" in interactive["confirms"][0]
    assert started == ["prova-1"]


def test_interactive_timed_practice_declined_does_not_start(logged_in_with_classroom, mock_practices, started, interactive):
    interactive["answers"] = ["prova-1"]
    interactive["confirm_answers"] = [False]
    result = runner.invoke(app, ["practices", "switch"])
    assert result.exit_code == 1
    assert started == []
    assert logged_in_with_classroom.get_active_practice() is None


def test_interactive_timed_practice_already_running_skips_the_confirm(logged_in_with_classroom, monkeypatch, started, interactive):
    running = [dict(FAKE_PRACTICES[1], attempt={"ends_at": "2026-07-23T11:00:00Z"})]
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: running)
    interactive["answers"] = ["prova-1"]
    result = runner.invoke(app, ["practices", "switch"])
    assert result.exit_code == 0, result.output
    assert interactive["confirms"] == []
    assert started == ["prova-1"]


def test_interactive_menu_disables_practices_outside_their_window(logged_in_with_classroom, monkeypatch, started, interactive):
    practices = [
        dict(FAKE_PRACTICES[0]),
        dict(FAKE_PRACTICES[0], slug="futura", title="Futura", window_status="upcoming"),
        dict(FAKE_PRACTICES[0], slug="velha", title="Velha", window_status="closed"),
    ]
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: practices)
    interactive["answers"] = ["turma-a-exercicios"]
    runner.invoke(app, ["practices", "switch"])
    reasons = {o.value: o.disabled_reason for o in interactive["menus"][0]["options"]}
    assert reasons == {"turma-a-exercicios": None, "futura": "not open yet", "velha": "closed"}


def test_interactive_menu_with_nothing_open_explains_instead_of_prompting(logged_in_with_classroom, monkeypatch, interactive):
    closed = [dict(FAKE_PRACTICES[0], window_status="closed")]
    monkeypatch.setattr(ApiClient, "list_practices", lambda self: closed)
    result = runner.invoke(app, ["practices", "switch"])
    assert result.exit_code == 1
    assert interactive["menus"] == []
    assert "No practice in this classroom is open right now." in result.output
