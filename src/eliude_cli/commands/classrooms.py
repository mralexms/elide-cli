from typing import Optional

import typer

from .. import config, prompts
from ..client import ApiError
from ..messages import t
from ..session import require_client
from . import practices


def _fetch_classrooms() -> list[dict]:
    client = require_client()
    try:
        return client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _print_classrooms(classrooms: list[dict]) -> None:
    if not classrooms:
        typer.echo(t("classrooms.none_enrolled"))
        raise typer.Exit(code=1)
    current = config.get_active_classroom()
    for c in classrooms:
        marker = "*" if c["slug"] == current else " "
        typer.echo(f"{marker} {c['slug']:<20} {c['name']}")


def list_classrooms() -> None:
    """List the classrooms you belong to, marking the active one."""
    _print_classrooms(_fetch_classrooms())


def switch(slug: Optional[str] = typer.Argument(None, help=t("help.arg.classrooms_switch_slug"))) -> None:
    """Switch the active classroom and then practice via interactive menus (the
    classroom menu is skipped when a slug is given). Outside a terminal there's
    no menu to draw: lists the classrooms, or just switches to the given slug."""
    classrooms = _fetch_classrooms()
    interactive = prompts.is_interactive()

    if slug is None:
        if not interactive:
            _print_classrooms(classrooms)
            return
        match = _choose_classroom(classrooms)
    else:
        match = next((c for c in classrooms if c["slug"] == slug), None)
        if match is None:
            typer.secho(t("classrooms.not_enrolled_in", slug=slug), fg=typer.colors.RED)
            raise typer.Exit(code=1)

    _activate(match)
    if interactive:
        practices.choose_practice(practices._fetch_practices())


def _choose_classroom(classrooms: list[dict]) -> dict:
    if not classrooms:
        typer.echo(t("classrooms.none_enrolled"))
        raise typer.Exit(code=1)
    current = config.get_active_classroom()
    options = [
        prompts.Option(
            f"{c['name']} {t('prompt.current')}" if c["slug"] == current else c["name"],
            value=c["slug"],
        )
        for c in classrooms
    ]
    slug = prompts.select(t("classrooms.choose"), options, default=current)
    if slug is None:
        typer.echo(t("prompt.cancelled"))
        raise typer.Exit(code=1)
    return next(c for c in classrooms if c["slug"] == slug)


def _activate(classroom: dict) -> None:
    config.set_active_classroom(classroom["slug"])
    config.clear_active_practice()
    typer.secho(t("classrooms.switched", name=classroom["name"], slug=classroom["slug"]), fg=typer.colors.GREEN)
