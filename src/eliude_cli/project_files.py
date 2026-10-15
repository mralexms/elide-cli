"""The files a question expects, and moving them between the server and a
local folder.

A plain question expects a single main.c; a project question declares its
own files (e.g. src/pilha.c), may accept more by pattern (src/*.c), and may
come with files the teacher provides (include/pilha.h, data/entrada.txt),
which the server always adds on its own — so they're never sent back.
"""

import fnmatch
from pathlib import Path, PurePosixPath

from .messages import t

DEFAULT_PATH = "main.c"


class ProjectFilesError(Exception):
    pass


def required_files(question: dict) -> list[str]:
    return question.get("required_files") or [DEFAULT_PATH]


def extra_patterns(question: dict) -> list[str]:
    return question.get("extra_file_patterns") or []


def provided_paths(question: dict) -> set[str]:
    return {f["path"] for f in question.get("files", []) if f.get("kind") != "student"}


def single_file_path(question: dict) -> str | None:
    """Where a lone file goes, or None when the question expects several."""
    required = required_files(question)
    if len(required) == 1 and not extra_patterns(question):
        return required[0]
    return None


def is_project(question: dict) -> bool:
    return single_file_path(question) != DEFAULT_PATH or bool(question.get("files"))


def _matches(path: str, pattern: str) -> bool:
    # Level by level, like the server: "src/*.c" takes src/a.c, not src/lib/a.c.
    parts, pattern_parts = path.split("/"), pattern.split("/")
    return len(parts) == len(pattern_parts) and all(
        fnmatch.fnmatchcase(part, pattern_part) for part, pattern_part in zip(parts, pattern_parts)
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ProjectFilesError(t("files.not_text", path=path))


def collect(question: dict, target: Path) -> dict[str, str]:
    """{path: content} to submit, from a single file or from a folder."""
    if target.is_file():
        path = single_file_path(question)
        if path is None:
            raise ProjectFilesError(t("files.needs_folder", files=", ".join(required_files(question))))
        return {path: _read(target)}

    required = required_files(question)
    patterns = extra_patterns(question)
    provided = provided_paths(question)
    files = {}
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        relative = path.relative_to(target).as_posix()
        if any(part.startswith(".") for part in PurePosixPath(relative).parts) or relative in provided:
            continue
        if relative in required or any(_matches(relative, pattern) for pattern in patterns):
            files[relative] = _read(path)

    missing = [path for path in required if path not in files]
    if missing:
        raise ProjectFilesError(t("files.missing", folder=target, files=", ".join(missing)))
    return files


def write_tree(folder: Path, files: dict[str, str], overwrite: bool) -> tuple[list[Path], list[Path]]:
    """Writes files under folder; returns (written, skipped). Existing files
    are only replaced with overwrite=True."""
    written, skipped = [], []
    root = folder.resolve()
    for relative, content in files.items():
        destination = folder / relative
        # Paths come from the server, which validates them — but never
        # write outside the folder on its word alone.
        if not destination.resolve().is_relative_to(root):
            raise ProjectFilesError(t("files.unsafe_path", path=relative))
        if destination.exists() and not overwrite:
            skipped.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
    return written, skipped
