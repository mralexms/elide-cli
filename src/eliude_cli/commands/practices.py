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


def is_finished(practice: dict) -> bool:
    """A finished practice (closed by the teacher or past its deadline) can
    still be read — questions, statements, your latest submission — but no
    longer accepts submissions."""
    return practice.get("window_status") == "closed"


def active_is_finished(client) -> bool:
    """Whether the active practice has finished (read-only). Best effort:
    False when the practice list can't be fetched, since this only decides
    whether to show a notice."""
    slug = config.get_active_practice()
    try:
        practices = client.list_practices()
    except ApiError:
        return False
    return any(p["slug"] == slug and is_finished(p) for p in practices)


def _print_practices(practices: list[dict]) -> None:
    """The open and upcoming practices, then the finished ones under their
    own heading."""
    if not practices:
        typer.echo(t("practices.none_yet"))
        raise typer.Exit(code=1)
    current = config.get_active_practice()

    def line(p: dict) -> str:
        marker = "*" if p["slug"] == current else " "
        window_label = typer.style(f"{p['window_status']:<9}", fg=_WINDOW_COLORS.get(p["window_status"]))
        timed_label = (
            t("practices.timed_label", minutes=p["duration_minutes"])
            if p["is_timed"]
            else t("practices.no_time_limit")
        )
        return f"{marker} {p['slug']:<25} {window_label} [{timed_label}] {p['title']}"

    active = [p for p in practices if not is_finished(p)]
    finished = [p for p in practices if is_finished(p)]
    for p in active:
        typer.echo(line(p))
    if finished:
        if active:
            typer.echo()
        typer.secho(t("practices.finished_heading"), bold=True)
        for p in finished:
            typer.echo(line(p))


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


# The menu entry that opens the finished practices (a value no slug can be).
_FINISHED_MENU = object()
_BACK = object()


def choose_practice(practices: list[dict]) -> None:
    """Interactive practice menu, then activates the choice. Upcoming
    practices are shown disabled (the backend refuses to start them);
    finished ones sit behind an "Finished practices (N)" entry that opens
    a second menu, where choosing one activates it read-only."""
    if not practices:
        typer.echo(t("practices.none_yet"))
        raise typer.Exit(code=1)

    current = config.get_active_practice()
    active = [p for p in practices if not is_finished(p)]
    finished = [p for p in practices if is_finished(p)]
    options = [
        prompts.Option(
            _practice_label(p, is_current=p["slug"] == current),
            value=p["slug"],
            disabled_reason=t("practices.window_upcoming") if p["window_status"] == "upcoming" else None,
        )
        for p in active
    ]
    if not finished and all(o.disabled_reason for o in options):
        _print_practices(practices)
        typer.secho(t("practices.none_open"), fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    if finished:
        options.append(prompts.Option(t("practices.finished_menu", count=len(finished)), value=_FINISHED_MENU))

    while True:
        slug = prompts.select(t("practices.choose"), options, default=current)
        if slug is None:
            typer.echo(t("prompt.cancelled"))
            raise typer.Exit(code=1)
        if slug is not _FINISHED_MENU:
            break
        slug = _choose_finished(finished, current)
        if slug is not _BACK:
            break

    match = next(p for p in practices if p["slug"] == slug)
    # Starting a timed practice starts its clock — make that explicit
    # unless the student already has a running attempt.
    if not is_finished(match) and match["is_timed"] and not match.get("attempt"):
        if not prompts.confirm(t("practices.confirm_start_timed", title=match["title"], minutes=match["duration_minutes"])):
            typer.echo(t("prompt.cancelled"))
            raise typer.Exit(code=1)

    _activate(match)


def _choose_finished(finished: list[dict], current: str | None):
    """The finished-practices menu: a slug, or _BACK for the main menu."""
    options = [prompts.Option(_practice_label(p, is_current=p["slug"] == current), value=p["slug"]) for p in finished]
    options.append(prompts.Option(t("practices.back"), value=_BACK))
    slug = prompts.select(t("practices.choose_finished"), options, default=current)
    if slug is None:
        typer.echo(t("prompt.cancelled"))
        raise typer.Exit(code=1)
    return slug


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
    if is_finished(practice):
        # Read-only: nothing to start (the backend refuses to start a
        # finished practice, and a timed one mustn't get an attempt now).
        config.set_active_practice(slug)
        typer.secho(t("practices.using", title=practice["title"], slug=slug), fg=typer.colors.GREEN)
        typer.secho(t("practices.read_only", title=practice["title"]), fg=typer.colors.YELLOW)
        return
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
