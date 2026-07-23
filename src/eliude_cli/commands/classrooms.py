from typing import Optional

import typer

from .. import config
from ..client import ApiError
from ..session import require_client


def _fetch_classrooms() -> list[dict]:
    client = require_client()
    try:
        return client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _print_classrooms(classrooms: list[dict]) -> None:
    if not classrooms:
        typer.echo("You are not enrolled in any classrooms yet.")
        raise typer.Exit(code=1)
    current = config.get_active_classroom()
    for c in classrooms:
        marker = "*" if c["slug"] == current else " "
        typer.echo(f"{marker} {c['slug']:<20} {c['name']}")


def list_classrooms() -> None:
    """List the classrooms you belong to, marking the active one."""
    _print_classrooms(_fetch_classrooms())


def switch(slug: Optional[str] = typer.Argument(None, help="Classroom slug to switch to")) -> None:
    """Switch the active classroom, or list the classrooms you belong to."""
    classrooms = _fetch_classrooms()

    if slug is None:
        _print_classrooms(classrooms)
        return

    match = next((c for c in classrooms if c["slug"] == slug), None)
    if match is None:
        typer.secho(f"You are not enrolled in classroom '{slug}'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config.set_active_classroom(slug)
    config.clear_active_practice()
    typer.secho(f"Switched to classroom '{match['name']}' ({slug}).", fg=typer.colors.GREEN)
