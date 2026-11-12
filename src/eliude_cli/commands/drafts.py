"""`eliude save` and `eliude load`: the student's code saved on the server
without grading (docs/plano-load-save.md, in eliude-server).

The server keeps one draft per question, overwritten on every save; only
`eliude submit` grades. `load` opens the newest version (draft, else latest
submission, else the question's starting files) in the editor from a
temporary folder and saves it back when the editor closes, if it changed.
Whatever goes wrong after the editor closes, the temporary folder stays and
its path is shown: the student's work is never thrown away.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import typer

from .. import editor, prompts
from ..client import ApiClient, ApiError
from ..formatting import parse_time, short_time
from ..messages import t
from ..project_files import ProjectFilesError, collect, provided_paths, required_files, single_file_path, write_tree
from ..session import require_practice_client
from .practices import active_is_finished


def _fail(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED)
    raise typer.Exit(code=1)


def _question(client: ApiClient, slug: str) -> dict:
    try:
        return client.get_question(slug)
    except ApiError as e:
        _fail(str(e))


def _files(entries: list[dict]) -> dict[str, str]:
    return {f["path"]: f["content"] for f in entries}


def save(
    slug: str,
    path: Optional[Path] = typer.Argument(None, exists=True, readable=True, help=t("help.arg.save_path")),
) -> None:
    """Save your code for a question on the server, without grading it."""
    client = require_practice_client()
    question = _question(client, slug)
    if path is None:
        # Like `eliude submit`: the project folder `show --download` made.
        path = Path(slug)
        if not path.is_dir():
            _fail(t("submit.no_path", slug=slug))
    try:
        files = collect(question, path)
    except ProjectFilesError as e:
        _fail(str(e))
    try:
        client.save_draft(slug, files)
    except ApiError as e:
        _fail(str(e))
    typer.secho(t("drafts.saved", slug=slug), fg=typer.colors.GREEN)


def _starting_point(client: ApiClient, slug: str, question: dict) -> tuple[dict[str, str], int, str]:
    """(files, draft version, where they came from) for `load`: the draft if
    it's newer than the latest submission, else the latest submission, else
    the question's starting files."""
    try:
        draft = client.get_draft(slug)
    except ApiError as e:
        _fail(str(e))
    try:
        submission = client.get_latest_submission(slug)
    except ApiError as e:
        if e.status != 404:
            _fail(str(e))
        submission = None

    version = draft["version"] if draft else 0
    if draft and submission:
        draft_time, submission_time = parse_time(draft["updated_at"]), parse_time(submission["created_at"])
        if draft_time and submission_time and submission_time > draft_time:
            draft = None
    if draft:
        return _files(draft["files"]), version, t("drafts.from_draft", when=short_time(draft["updated_at"]))
    if submission:
        files = _files(submission.get("files") or []) or {required_files(question)[0]: submission.get("source_code", "")}
        return files, version, t("drafts.from_submission", when=short_time(submission["created_at"]))

    student = {f["path"]: f["content"] for f in question.get("files", []) if f.get("kind") == "student"}
    files = {path: student.get(path, "") for path in required_files(question)}
    return files, version, t("drafts.from_start")


def _keep(folder: Path, retry: Path, slug: str, can_retry: bool = True) -> None:
    """Leaves the files where they are and, when saving later can work,
    says how."""
    typer.secho(t("drafts.kept", folder=folder), fg=typer.colors.YELLOW)
    if can_retry:
        typer.echo(t("drafts.retry", command=f"eliude save {slug} {retry}"))
    raise typer.Exit(code=1)


def _local_place(question: dict, path: Path, files: dict[str, str], overwrite: bool) -> tuple[Path, Path, dict[Path, str]]:
    """Where `load q1 <path>` puts the files: (folder of the tree, what a
    save reads back — the file itself or the folder, {file: content}). A
    single-file question takes a file (or a folder, where the file goes by
    its own name); a project, a folder. Asks before replacing a file whose
    content differs."""
    single = single_file_path(question)
    if single is None and path.is_file():
        _fail(t("files.needs_folder", files=", ".join(required_files(question))))
    if single is not None and not path.is_dir():
        # The student's own name for the file (q1.c) holds the one file.
        targets = {path: next(iter(files.values()))}
        folder, retry = path.parent, path
    else:
        targets = {path / relative: content for relative, content in files.items()}
        folder = retry = path

    differs = [
        p for p, content in targets.items() if p.exists() and p.read_text(encoding="utf-8", errors="replace") != content
    ]
    if differs and not overwrite:
        names = ", ".join(str(p) for p in differs)
        if not prompts.is_interactive():
            _fail(t("drafts.local_exists_no_terminal", files=names))
        if not prompts.confirm(t("drafts.local_overwrite", files=names)):
            typer.echo(t("prompt.cancelled"))
            raise typer.Exit(code=1)
    return folder, retry, targets


def load(
    slug: str,
    path: Optional[Path] = typer.Argument(None, help=t("help.arg.load_path")),
    overwrite: bool = typer.Option(False, "--overwrite", help=t("help.opt.load_overwrite")),
) -> None:
    """Open your latest code for a question in your editor; saving it there
    saves it on the server, without grading. With a path, the code goes to
    that file (or project folder), which stays there."""
    client = require_practice_client()
    question = _question(client, slug)
    files, version, origin = _starting_point(client, slug, question)
    read_only = active_is_finished(client)
    provided = {f["path"]: f["content"] for f in question.get("files", []) if f["path"] in provided_paths(question)}

    temporary = path is None
    folder = None
    try:
        if temporary:
            folder = Path(tempfile.mkdtemp(prefix=f"eliude-{slug}-"))
            # The teacher's files too, so a project can be read (and built)
            # whole; only the student's go back to the server.
            write_tree(folder, {**provided, **files}, overwrite=True)
            single = single_file_path(question)
            retry = folder / single if single else folder
            opened = [folder / relative for relative in files]
        else:
            folder, retry, targets = _local_place(question, path, files, overwrite)
            if retry == folder:
                # Folder mode (a project): the teacher's files go in too, but
                # a local copy that's already there is left alone.
                write_tree(folder, provided, overwrite=False)
            for target, content in targets.items():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            opened = list(targets)
    except (ProjectFilesError, OSError) as e:
        if temporary and folder is not None:
            shutil.rmtree(folder, ignore_errors=True)
        _fail(str(e))

    def done() -> None:
        if temporary:
            shutil.rmtree(folder, ignore_errors=True)

    typer.echo(origin)
    if not temporary:
        typer.echo(t("drafts.written_to", path=retry))
    if read_only:
        typer.secho(t("drafts.read_only"), fg=typer.colors.YELLOW)

    try:
        finished_normally = editor.edit(opened)
    except editor.EditorError:
        done()
        _fail(t("drafts.no_editor"))

    try:
        edited = collect(question, retry)
    except ProjectFilesError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        _keep(folder, retry, slug)

    if edited == files:
        done()
        typer.echo(t("drafts.unchanged"))
        return
    if not finished_normally:
        typer.secho(t("drafts.editor_failed"), fg=typer.colors.YELLOW)
        _keep(folder, retry, slug)
    if read_only:
        typer.secho(t("drafts.not_saved_finished"), fg=typer.colors.YELLOW)
        _keep(folder, retry, slug, can_retry=False)

    try:
        client.save_draft(slug, edited, base_version=version)
    except ApiError as e:
        if e.code != "draft_conflict":
            typer.secho(str(e), fg=typer.colors.RED)
            _keep(folder, retry, slug)
        if not prompts.is_interactive():
            typer.secho(t("drafts.conflict_not_saved"), fg=typer.colors.YELLOW)
            _keep(folder, retry, slug)
        if not prompts.confirm(t("drafts.conflict")):
            _keep(folder, retry, slug)
        try:
            client.save_draft(slug, edited)
        except ApiError as e2:
            typer.secho(str(e2), fg=typer.colors.RED)
            _keep(folder, retry, slug)

    done()
    typer.secho(t("drafts.saved", slug=slug), fg=typer.colors.GREEN)
    typer.echo(t("drafts.how_to_grade", slug=slug))
