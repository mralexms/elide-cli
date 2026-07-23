import typer

from .. import config
from ..client import ApiClient, ApiError
from ..session import require_client


def _fetch_practices(classroom_slug: str) -> list[dict]:
    scoped_client = ApiClient(config.get_base_url(), token=config.get_token(), classroom=classroom_slug)
    return scoped_client.list_practices()


def _fetch_questions(classroom_slug: str, practice_slug: str) -> list[dict]:
    scoped_client = ApiClient(
        config.get_base_url(), token=config.get_token(), classroom=classroom_slug, practice=practice_slug
    )
    return scoped_client.list_exercises()


def _print_stats(questions: list[dict], indent: str = "") -> None:
    total = len(questions)
    passed = sum(1 for q in questions if q.get("status") == "success")
    failed = sum(1 for q in questions if q.get("status") == "failure")
    score = (passed / total * 100) if total else 0.0
    typer.echo(f"{indent}Questions: {total}")
    typer.secho(f"{indent}Passed: {passed}", fg=typer.colors.GREEN)
    typer.secho(f"{indent}Failed: {failed}", fg=typer.colors.RED)
    typer.echo(f"{indent}Score: {score:.1f}% ({passed}/{total})")


def status(
    all_classrooms: bool = typer.Option(
        False, "--all", help="Show stats for every practice in every classroom you belong to"
    ),
) -> None:
    """Show your login, active classroom/practice, and question stats."""
    client = require_client()
    typer.echo(f"Logged in as: {config.get_username()}")

    try:
        classrooms = client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    active_classroom_slug = config.get_active_classroom()

    if all_classrooms:
        if not classrooms:
            typer.echo("You are not enrolled in any classrooms yet.")
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
                typer.echo("    No practices yet.")
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
        typer.secho("No active classroom set. Run `eliude switch` first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    match = next((c for c in classrooms if c["slug"] == active_classroom_slug), None)
    if match is None:
        typer.secho(f"You are not enrolled in classroom '{active_classroom_slug}'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    active_practice_slug = config.get_active_practice()
    if active_practice_slug is None:
        typer.secho("No active practice set. Run `eliude practices switch` first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Classroom: {match['name']} ({match['slug']})")
    typer.echo(f"Practice: {active_practice_slug}")
    try:
        questions = _fetch_questions(active_classroom_slug, active_practice_slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    _print_stats(questions)
