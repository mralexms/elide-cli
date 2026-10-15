from pathlib import Path

import typer

from ..client import ApiError
from ..messages import t
from ..project_files import ProjectFilesError, write_tree
from ..session import require_practice_client


def _submission_files(submission: dict) -> dict[str, str]:
    files = submission.get("files")
    if files:
        return {f["path"]: f["content"] for f in files}
    return {"main.c": submission.get("source_code", "")}


def get(
    slug: str,
    save: bool = typer.Option(False, "--save", help=t("help.opt.get_save")),
    overwrite: bool = typer.Option(False, "--overwrite", help=t("help.opt.get_overwrite")),
) -> None:
    """Show your latest submission for a question in the active practice."""
    client = require_practice_client()
    try:
        submission = client.get_latest_submission(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    files = _submission_files(submission)
    single = len(files) == 1

    if not save:
        if single:
            typer.echo(next(iter(files.values())))
            return
        for path, content in files.items():
            typer.secho(f"== {path} ==", bold=True)
            typer.echo(content)
        return

    if single:
        target = Path(f"{slug}.c")
        if target.exists() and not overwrite:
            typer.echo(t("get.file_exists", target=target))
            if not typer.confirm(t("get.overwrite_prompt"), default=False):
                target = Path(typer.prompt(t("get.enter_filename_prompt")))

        target.write_text(next(iter(files.values())))
        typer.secho(t("get.saved", slug=slug, target=target), fg=typer.colors.GREEN)
        return

    # A project goes back to ./<slug>/, the folder `eliude submit` reads.
    folder = Path(slug)
    existing = [folder / path for path in files if (folder / path).exists()]
    if existing and not overwrite:
        typer.echo(t("get.files_exist", count=len(existing), folder=folder))
        if not typer.confirm(t("get.overwrite_prompt"), default=False):
            raise typer.Exit(code=1)
    try:
        write_tree(folder, files, overwrite=True)
    except ProjectFilesError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho(t("get.saved_folder", slug=slug, count=len(files), folder=folder), fg=typer.colors.GREEN)
