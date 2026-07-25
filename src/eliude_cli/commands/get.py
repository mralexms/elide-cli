from pathlib import Path

import typer

from ..client import ApiError
from ..messages import t
from ..session import require_practice_client


def get(
    slug: str,
    save: bool = typer.Option(False, "--save", help="Save to <slug>.c instead of printing to stdout"),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="With --save, overwrite the destination file without prompting"
    ),
) -> None:
    """Show your latest submission for a question in the active practice."""
    client = require_practice_client()
    try:
        submission = client.get_latest_submission(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not save:
        typer.echo(submission["source_code"])
        return

    target = Path(f"{slug}.c")
    if target.exists() and not overwrite:
        typer.echo(t("get.file_exists", target=target))
        if not typer.confirm(t("get.overwrite_prompt"), default=False):
            target = Path(typer.prompt(t("get.enter_filename_prompt")))

    target.write_text(submission["source_code"])
    typer.secho(t("get.saved", slug=slug, target=target), fg=typer.colors.GREEN)
