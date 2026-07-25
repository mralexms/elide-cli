import typer

from .. import config
from ..client import ApiClient, ApiError
from ..messages import t
from ..session import anonymous_client, require_client


def _print_server_status() -> None:
    base_url = config.get_base_url()
    try:
        health = anonymous_client().get_health()
    except ApiError as e:
        typer.secho(t("status.server_unreachable", url=base_url, error=e), fg=typer.colors.RED)
        return
    typer.secho(
        t("status.server_reachable", url=base_url, version=health.get("version", "?")), fg=typer.colors.GREEN
    )


def _fetch_practices(classroom_slug: str) -> list[dict]:
    scoped_client = ApiClient(config.get_base_url(), token=config.get_token(), classroom=classroom_slug)
    return scoped_client.list_practices()


def _fetch_questions(classroom_slug: str, practice_slug: str) -> list[dict]:
    scoped_client = ApiClient(
        config.get_base_url(), token=config.get_token(), classroom=classroom_slug, practice=practice_slug
    )
    return scoped_client.list_questions()


def _print_stats(questions: list[dict], indent: str = "") -> None:
    total = len(questions)
    passed = sum(1 for q in questions if q.get("status") == "success")
    failed = sum(1 for q in questions if q.get("status") == "failure")
    score = (passed / total * 100) if total else 0.0
    typer.echo(f"{indent}{t('status.questions_label', total=total)}")
    typer.secho(f"{indent}{t('status.passed_label', passed=passed)}", fg=typer.colors.GREEN)
    typer.secho(f"{indent}{t('status.failed_label', failed=failed)}", fg=typer.colors.RED)
    typer.echo(f"{indent}{t('status.score_label', score=f'{score:.1f}', passed=passed, total=total)}")


def status(
    all_classrooms: bool = typer.Option(False, "--all", help=t("help.opt.status_all")),
) -> None:
    """Show your login, active classroom/practice, and question stats."""
    _print_server_status()

    client = require_client()
    typer.echo(t("status.logged_in_as", username=config.get_username()))

    try:
        classrooms = client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    active_classroom_slug = config.get_active_classroom()

    if all_classrooms:
        if not classrooms:
            typer.echo(t("classrooms.none_enrolled"))
            return
        for i, c in enumerate(classrooms):
            if i > 0:
                typer.echo()
            marker = "*" if c["slug"] == active_classroom_slug else " "
            typer.echo(f"{marker} {c['name']} ({c['slug']})")
            try:
                practices = _fetch_practices(c["slug"])
            except ApiError as e:
                typer.secho(f"    {e}", fg=typer.colors.RED)
                continue
            if not practices:
                typer.echo(f"    {t('status.no_practices_yet')}")
                continue
            for practice in practices:
                typer.echo(f"    {practice['title']} ({practice['slug']})")
                try:
                    questions = _fetch_questions(c["slug"], practice["slug"])
                except ApiError as e:
                    typer.secho(f"        {e}", fg=typer.colors.RED)
                    continue
                _print_stats(questions, indent="        ")
        return

    if active_classroom_slug is None:
        typer.secho(t("session.no_active_classroom"), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    match = next((c for c in classrooms if c["slug"] == active_classroom_slug), None)
    if match is None:
        typer.secho(t("classrooms.not_enrolled_in", slug=active_classroom_slug), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    active_practice_slug = config.get_active_practice()
    if active_practice_slug is None:
        typer.secho(t("session.no_active_practice"), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(t("status.classroom_label", name=match["name"], slug=match["slug"]))
    typer.echo(t("status.practice_label", slug=active_practice_slug))
    try:
        questions = _fetch_questions(active_classroom_slug, active_practice_slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    _print_stats(questions)
