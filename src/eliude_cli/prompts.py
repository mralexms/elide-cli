"""Interactive menus (arrow keys or number shortcuts), used by the switch
commands when no slug is given. Kept behind this small wrapper so commands
can fall back to plain listing when there's no terminal to draw a menu on
(scripts, pipes, CliRunner in tests), and so tests can stub the prompts
without driving prompt_toolkit.
"""

import sys
from typing import Any, Optional

import questionary

from .messages import t

# questionary's shortcut keys are 1-9, 0, then a-z: 36 in total.
_MAX_SHORTCUTS = 36


class Option:
    def __init__(self, label: str, value: Any, disabled_reason: Optional[str] = None):
        self.label = label
        self.value = value
        self.disabled_reason = disabled_reason


def is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def select(message: str, options: list[Option], default: Any = None) -> Optional[Any]:
    """Returns the chosen option's value, or None if the user cancelled (Ctrl+C)."""
    choices = [questionary.Choice(o.label, value=o.value, disabled=o.disabled_reason) for o in options]
    enabled_values = [o.value for o in options if o.disabled_reason is None]
    use_shortcuts = len(choices) <= _MAX_SHORTCUTS
    return questionary.select(
        message,
        choices=choices,
        default=default if default in enabled_values else None,
        use_shortcuts=use_shortcuts,
        # j/k would collide with the letter shortcuts past the 10th option.
        use_jk_keys=False,
        instruction=t("prompt.select_instruction" if use_shortcuts else "prompt.select_instruction_arrows"),
    ).ask()


def confirm(message: str) -> bool:
    return bool(questionary.confirm(message, default=False).ask())
