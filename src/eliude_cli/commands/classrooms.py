from typing import Optional

import typer

from .. import config
from ..client import ApiError
from ..session import require_client


def switch(slug: Optional[str] = typer.Argument(None, help="Classroom slug to switch to")) -> None:
    """Switch the active classroom, or list the classrooms you belong to."""
    client = require_client()
    try:
        classrooms = client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not classrooms:
        typer.echo("You are not enrolled in any classrooms yet.")
        raise typer.Exit(code=1)

    if slug is None:
        current = config.get_active_classroom()
        for c in classrooms:
            marker = "*" if c["slug"] == current else " "
            typer.echo(f"{marker} {c['slug']:<20} {c['name']}")
        return

    match = next((c for c in classrooms if c["slug"] == slug), None)
    if match is None:
        typer.secho(f"You are not enrolled in classroom '{slug}'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config.set_active_classroom(slug)
    typer.secho(f"Switched to classroom '{match['name']}' ({slug}).", fg=typer.colors.GREEN)
