from typing import Optional

import typer

from .. import config
from ..client import ApiError
from ..messages import t
from ..session import require_classroom_client

_WINDOW_COLORS = {
    "open": typer.colors.GREEN,
    "upcoming": typer.colors.YELLOW,
    "closed": typer.colors.RED,
}


def _fetch_practices() -> list[dict]:
    client = require_classroom_client()
    try:
        return client.list_practices()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _print_practices(practices: list[dict]) -> None:
    if not practices:
        typer.echo(t("practices.none_yet"))
        raise typer.Exit(code=1)
    current = config.get_active_practice()
    for p in practices:
        marker = "*" if p["slug"] == current else " "
        window_label = typer.style(f"{p['window_status']:<9}", fg=_WINDOW_COLORS.get(p["window_status"]))
        timed_label = (
            t("practices.timed_label", minutes=p["duration_minutes"])
            if p["is_timed"]
            else t("practices.no_time_limit")
        )
        typer.echo(f"{marker} {p['slug']:<25} {window_label} [{timed_label}] {p['title']}")


def list_practices() -> None:
    """List the practices available in the active classroom, marking the active one."""
    _print_practices(_fetch_practices())


def switch(slug: Optional[str] = typer.Argument(None, help="Practice slug to switch to")) -> None:
    """Switch the active practice, or list the practices available in the active classroom."""
    practices = _fetch_practices()

    if slug is None:
        _print_practices(practices)
        return

    match = next((p for p in practices if p["slug"] == slug), None)
    if match is None:
        typer.secho(t("practices.not_found", slug=slug), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    client = require_classroom_client()
    try:
        result = client.start_practice(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config.set_active_practice(slug)
    typer.secho(t("practices.using", title=match["title"], slug=slug), fg=typer.colors.GREEN)

    attempt = result.get("attempt")
    if attempt:
        typer.secho(t("practices.time_limit_ends", ends_at=attempt["ends_at"]), fg=typer.colors.YELLOW)
