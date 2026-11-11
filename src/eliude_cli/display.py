"""Formatted output for long texts, like a question's statement: Markdown
rendered with colours (256 by default) and shown through `less` when it
doesn't fit the screen, the way `git log` does.

When stdout isn't a terminal (a pipe, a file) the text goes out plain, with
no colours and no pager, so `eliude show q1 > q1.txt` keeps working.
"""

import io
import os
import shlex
import subprocess
import sys
from shutil import get_terminal_size
from typing import Callable

from rich import box
from rich.cells import cell_len
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

# Wider than this, Markdown paragraphs get hard to read.
MAX_WIDTH = 100

_COLOR_CHOICES = {"16": "standard", "256": "256", "truecolor": "truecolor"}


def color_system() -> str | None:
    """256 colours by default: most terminals that call themselves "xterm"
    (PuTTY, macOS Terminal, VS Code) handle them without saying so in $TERM,
    and macOS Terminal mangles truecolor. ELIUDE_COLORS=16|256|truecolor|none
    overrides it; NO_COLOR turns colours off."""
    choice = os.environ.get("ELIUDE_COLORS", "").strip().lower()
    if choice in _COLOR_CHOICES:
        return _COLOR_CHOICES[choice]
    if choice == "none" or "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return None
    if sys.platform == "win32":
        # Old Windows consoles have no ANSI support: let rich find out.
        return "auto"
    return "256"


class StatementMarkdown(Markdown):
    """Markdown that keeps single line breaks, as the portal does: plain-text
    statements written before Markdown would otherwise run together."""

    def __init__(self, markup: str, **kwargs) -> None:
        super().__init__(markup, **kwargs)
        for token in self.parsed:
            for child in token.children or []:
                if child.type == "softbreak":
                    child.type = "hardbreak"


def statement(text: str, console: Console) -> StatementMarkdown:
    # The 16 basic colours take the terminal's own palette; monokai's
    # background would otherwise be approximated badly.
    theme = "ansi_dark" if console.color_system == "standard" else "monokai"
    # No OSC 8 links: older `less` shows them as garbage.
    return StatementMarkdown(text, code_theme=theme, hyperlinks=False)


def sample_table(stdin: str, expected: str, labels: tuple[str, str], empty: str, width: int, indent: int = 2):
    """A sample test case as two columns, input beside expected output, or
    None when some line doesn't fit its column: folding it would look like
    a line break that isn't there, so the caller prints them one under the
    other instead. `stdin`/`expected` already have plain newlines."""
    # Rounded box, one space of padding on each side: 3 borders + 4 spaces.
    column = (width - indent - 7) // 2
    if any(cell_len(label) > column for label in labels):
        return None
    cells = []
    for value in (stdin, expected):
        lines = value.rstrip("\n").split("\n")
        if any(cell_len(line) > column for line in lines):
            return None
        cells.append(Text(value.rstrip("\n")) if value.strip("\n") else Text(empty, style="dim"))

    table = Table(box=box.ROUNDED, header_style="bold", show_lines=False, pad_edge=True)
    for label in labels:
        table.add_column(label, no_wrap=True, overflow="ignore")
    table.add_row(*cells)
    return Padding(table, (0, 0, 0, indent))


def _console(**kwargs) -> Console:
    return Console(highlight=False, markup=False, emoji=False, **kwargs)


def show(render: Callable[[Console, bool], None]) -> None:
    """Calls render(console, formatted) and shows what it printed: plain when
    stdout isn't a terminal, otherwise formatted and through the pager."""
    if not sys.stdout.isatty():
        render(_console(file=sys.stdout, color_system=None, soft_wrap=True), False)
        return

    colors = color_system()
    width = min(get_terminal_size().columns, MAX_WIDTH)
    pager = _pager_command()
    if pager is None:
        render(_console(color_system=colors, width=width), True)
        return

    buffer = io.StringIO()
    render(_console(file=buffer, force_terminal=colors is not None, color_system=colors, width=width), True)
    if not _run_pager(pager, buffer.getvalue()):
        sys.stdout.write(buffer.getvalue())


def _pager_command() -> list[str] | None:
    if sys.platform == "win32":
        # No `less` there, and the fallback (`more`) shows colours as garbage.
        return None
    return shlex.split(os.environ.get("PAGER") or "less") or None


def _run_pager(command: list[str], text: str) -> bool:
    """Pipes `text` into the pager. False when it couldn't show it: the
    program doesn't exist or exited with an error (a broken PAGER, say), so
    the caller prints the text instead. `less` itself exits 0 even when the
    student quits early or LESS has an unknown option."""
    env = dict(os.environ)
    # Like git: quit if it fits one screen (F), keep colours (R), leave the
    # text on the screen after quitting (X). A LESS of the user's own wins.
    env.setdefault("LESS", "FRX")
    env.setdefault("LESSCHARSET", "utf-8")
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, env=env)
    except OSError:
        return False
    try:
        process.stdin.write(text.encode("utf-8"))
        process.stdin.close()
    except BrokenPipeError:
        # The student quit the pager before reading it all.
        pass
    while True:
        try:
            return process.wait() == 0
        except KeyboardInterrupt:
            # Ctrl+C is the pager's business; wait for it to quit.
            pass
