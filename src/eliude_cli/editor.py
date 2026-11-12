"""Opening files in the student's editor and waiting for it to close, the
way `git commit` does: $VISUAL, then $EDITOR, then the first of vim, vi and
nano that exists (notepad on Windows).

A graphical editor must be told to wait for its window to close
(`code --wait`, `subl -w`), or the CLI would see it "close" right away.
"""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

_FALLBACKS = ("vim", "vi", "nano")


class EditorError(Exception):
    pass


def command() -> list[str] | None:
    """The editor command, split like a shell would, or None if there's no
    editor to be found."""
    for name in ("VISUAL", "EDITOR"):
        value = os.environ.get(name, "").strip()
        if value:
            return shlex.split(value, posix=sys.platform != "win32")
    if sys.platform == "win32":
        return ["notepad"]
    for fallback in _FALLBACKS:
        if shutil.which(fallback):
            return [fallback]
    return None


def edit(paths: list[Path]) -> bool:
    """Opens `paths` in the editor and waits. True if the editor exited
    normally; False if it exited with an error (vim's `:cq`, for one), which
    means "don't use what I did", as for git. Raises EditorError when the
    editor can't be started."""
    editor = command()
    if editor is None:
        raise EditorError("no editor")
    # Notepad opens one file at a time: a project's files go one after the other.
    one_at_a_time = Path(editor[0]).name.lower() in ("notepad", "notepad.exe")
    batches = [[path] for path in paths] if one_at_a_time else [paths]
    for batch in batches:
        try:
            result = subprocess.run([*editor, *(str(path) for path in batch)])
        except OSError as e:
            raise EditorError(str(e)) from e
        if result.returncode != 0:
            return False
    return True
