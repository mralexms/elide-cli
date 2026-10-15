from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..client import ApiError
from ..formatting import print_submission_result
from ..messages import t
from ..project_files import ProjectFilesError, collect
from ..session import require_practice_client


def submit(
    slug: str,
    path: Optional[Path] = typer.Argument(None, exists=True, readable=True, help=t("help.arg.submit_path")),
) -> None:
    """Submit a C solution for a question in the active practice."""
    client = require_practice_client()
    try:
        question = client.get_question(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if path is None:
        # `eliude show <slug> --download` lays a project out in ./<slug>/.
        path = Path(slug)
        if not path.is_dir():
            typer.secho(t("submit.no_path", slug=slug), fg=typer.colors.RED)
            raise typer.Exit(code=1)

    try:
        files = collect(question, path)
    except ProjectFilesError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if path.is_dir():
        size = sum(len(content.encode("utf-8")) for content in files.values())
        typer.echo(t("submit.sending_files", count=len(files), kb=f"{size / 1000:.1f}"))
        for relative in files:
            typer.echo(f"  {relative}")

    try:
        with Console().status(t("submit.grading"), spinner="dots"):
            result = client.submit(slug, files)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    print_submission_result(result)
    if result["status"] not in ("passed",):
        raise typer.Exit(code=1)
