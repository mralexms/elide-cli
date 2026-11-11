import io

import pytest

from eliude_cli import display

STATEMENT = "# Soma\n\nLeia **N** números.\nImprima a soma.\n\n```c\nint main(void) { return 0; }\n```\n"


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("ELIUDE_COLORS", "NO_COLOR", "PAGER", "LESS", "LESSCHARSET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setattr(display.sys, "platform", "darwin")


class FakeStdout(io.StringIO):
    def __init__(self, tty):
        super().__init__()
        self.tty = tty

    def isatty(self):
        return self.tty


class FakePager:
    """Stands in for subprocess.Popen, keeping what was piped into it."""

    calls = []

    def __init__(self, command, stdin, env):
        self.command, self.env = command, env
        self.stdin = io.BytesIO()
        self.stdin.close = lambda: None
        FakePager.calls.append(self)

    def wait(self):
        return 0

    @property
    def text(self):
        return self.stdin.getvalue().decode("utf-8")


@pytest.fixture
def fake_pager(monkeypatch):
    FakePager.calls = []
    monkeypatch.setattr(display.subprocess, "Popen", FakePager)
    return FakePager


def render_statement(console, formatted):
    console.print(display.statement(STATEMENT, console) if formatted else STATEMENT)


def test_uses_256_colours_even_when_term_does_not_say_so(clean_env):
    assert display.color_system() == "256"


@pytest.mark.parametrize("value, expected", [("16", "standard"), ("256", "256"), ("truecolor", "truecolor"), ("none", None)])
def test_eliude_colors_overrides_the_default(clean_env, monkeypatch, value, expected):
    monkeypatch.setenv("ELIUDE_COLORS", value)
    assert display.color_system() == expected


def test_no_color_turns_colours_off(clean_env, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert display.color_system() is None


def test_single_line_breaks_are_kept_like_on_the_portal(clean_env):
    console = display._console(file=io.StringIO(), color_system=None, width=80)
    console.print(display.statement("primeira linha\nsegunda linha", console))
    lines = [line.rstrip() for line in console.file.getvalue().splitlines()]
    assert lines == ["primeira linha", "segunda linha"]


def test_piped_output_is_the_plain_statement_without_pager(clean_env, monkeypatch, fake_pager):
    out = FakeStdout(tty=False)
    monkeypatch.setattr(display.sys, "stdout", out)
    display.show(render_statement)
    assert out.getvalue() == STATEMENT + "\n"
    assert fake_pager.calls == []


def test_terminal_output_goes_through_less_formatted_in_256_colours(clean_env, monkeypatch, fake_pager):
    monkeypatch.setattr(display.sys, "stdout", FakeStdout(tty=True))
    display.show(render_statement)
    [pager] = fake_pager.calls
    assert pager.command == ["less"]
    assert pager.env["LESS"] == "FRX"
    assert "**" not in pager.text and "```" not in pager.text
    assert "\x1b[1m" in pager.text  # bold N
    assert "\x1b[38;5;" in pager.text  # 256-colour code
    assert "\x1b[38;2;" not in pager.text  # no truecolor


def test_the_users_own_less_and_pager_win(clean_env, monkeypatch, fake_pager):
    monkeypatch.setenv("LESS", "-R")
    monkeypatch.setenv("PAGER", "most -s")
    monkeypatch.setattr(display.sys, "stdout", FakeStdout(tty=True))
    display.show(render_statement)
    [pager] = fake_pager.calls
    assert pager.command == ["most", "-s"]
    assert pager.env["LESS"] == "-R"


def test_falls_back_to_printing_when_the_pager_is_missing(clean_env, monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("less")

    out = FakeStdout(tty=True)
    monkeypatch.setattr(display.sys, "stdout", out)
    monkeypatch.setattr(display.subprocess, "Popen", missing)
    display.show(render_statement)
    assert "Soma" in out.getvalue() and "**" not in out.getvalue()


@pytest.mark.parametrize("exit_code", [1, 127])
def test_falls_back_to_printing_when_the_pager_fails(clean_env, monkeypatch, exit_code):
    class FailingPager(FakePager):
        def wait(self):
            return exit_code

    FakePager.calls = []
    out = FakeStdout(tty=True)
    monkeypatch.setattr(display.sys, "stdout", out)
    monkeypatch.setattr(display.subprocess, "Popen", FailingPager)
    display.show(render_statement)
    assert "Soma" in out.getvalue() and "**" not in out.getvalue()


def test_a_pager_that_succeeds_is_not_followed_by_a_second_copy(clean_env, monkeypatch, fake_pager):
    out = FakeStdout(tty=True)
    monkeypatch.setattr(display.sys, "stdout", out)
    display.show(render_statement)
    assert out.getvalue() == ""


def test_no_pager_on_windows(clean_env, monkeypatch, fake_pager):
    monkeypatch.setattr(display.sys, "platform", "win32")
    monkeypatch.setattr(display.sys, "stdout", FakeStdout(tty=True))
    assert display._pager_command() is None


def render_table(table, width=80):
    from rich.console import Console

    console = Console(file=io.StringIO(), width=width, color_system=None)
    console.print(table)
    return "\n".join(line.rstrip() for line in console.file.getvalue().splitlines())


LABELS = ("Entrada", "Saída esperada")


def test_sample_table_puts_input_beside_expected_output():
    table = display.sample_table("3\n1 2 3\n", "6\n", LABELS, "(vazia)", 80)
    assert render_table(table) == (
        "  ╭─────────┬────────────────╮\n"
        "  │ Entrada │ Saída esperada │\n"
        "  ├─────────┼────────────────┤\n"
        "  │ 3       │ 6              │\n"
        "  │ 1 2 3   │                │\n"
        "  ╰─────────┴────────────────╯"
    )


def test_sample_table_marks_an_empty_input():
    assert "│ (vazia) │ 0" in render_table(display.sample_table("", "0\n", LABELS, "(vazia)", 80))


def test_no_table_when_a_line_would_have_to_fold():
    # Folding would look like a line break that isn't in the test case.
    assert display.sample_table("x" * 40 + "\n", "ok\n", LABELS, "(vazia)", 80) is None
    assert display.sample_table("a\n", "b\n", LABELS, "(vazia)", 30) is None  # labels don't fit either
