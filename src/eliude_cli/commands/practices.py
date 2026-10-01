from typing import Optional

import typer

from .. import config, prompts
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


def switch(slug: Optional[str] = typer.Argument(None, help=t("help.arg.practices_switch_slug"))) -> None:
    """Switch the active practice: interactive menu without a slug (plain list when not in a terminal)."""
    practices = _fetch_practices()

    if slug is None:
        if not prompts.is_interactive():
            _print_practices(practices)
            return
        choose_practice(practices)
        return

    match = next((p for p in practices if p["slug"] == slug), None)
    if match is None:
        typer.secho(t("practices.not_found", slug=slug), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    _activate(match)


def choose_practice(practices: list[dict]) -> None:
    """Interactive practice menu, then activates the choice. Practices outside
    their window are shown disabled — the backend refuses to start them."""
    if not practices:
        typer.echo(t("practices.none_yet"))
        raise typer.Exit(code=1)

    disabled_reasons = {"upcoming": t("practices.window_upcoming"), "closed": t("practices.window_closed")}
    current = config.get_active_practice()
    options = [
        prompts.Option(
            _practice_label(p, is_current=p["slug"] == current),
            value=p["slug"],
            disabled_reason=disabled_reasons.get(p["window_status"]),
        )
        for p in practices
    ]
    if all(o.disabled_reason for o in options):
        _print_practices(practices)
        typer.secho(t("practices.none_open"), fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    slug = prompts.select(t("practices.choose"), options, default=current)
    if slug is None:
        typer.echo(t("prompt.cancelled"))
        raise typer.Exit(code=1)

    match = next(p for p in practices if p["slug"] == slug)
    # Starting a timed practice starts its clock — make that explicit
    # unless the student already has a running attempt.
    if match["is_timed"] and not match.get("attempt"):
        if not prompts.confirm(t("practices.confirm_start_timed", title=match["title"], minutes=match["duration_minutes"])):
            typer.echo(t("prompt.cancelled"))
            raise typer.Exit(code=1)

    _activate(match)


def _practice_label(practice: dict, is_current: bool) -> str:
    timed_label = (
        t("practices.timed_label", minutes=practice["duration_minutes"])
        if practice["is_timed"]
        else t("practices.no_time_limit")
    )
    label = f"{practice['title']} [{timed_label}]"
    return f"{label} {t('prompt.current')}" if is_current else label


def _activate(practice: dict) -> None:
    slug = practice["slug"]
    client = require_classroom_client()
    try:
        result = client.start_practice(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config.set_active_practice(slug)
    typer.secho(t("practices.using", title=practice["title"], slug=slug), fg=typer.colors.GREEN)

    attempt = result.get("attempt")
    if attempt:
        typer.secho(t("practices.time_limit_ends", ends_at=attempt["ends_at"]), fg=typer.colors.YELLOW)
