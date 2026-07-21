import typer

from .. import config
from ..client import ApiClient, ApiError
from ..session import require_client


def _fetch_exercises(classroom_slug: str) -> list[dict]:
    scoped_client = ApiClient(config.get_base_url(), token=config.get_token(), classroom=classroom_slug)
    return scoped_client.list_exercises()


def _print_stats(exercises: list[dict], indent: str = "") -> None:
    total = len(exercises)
    passed = sum(1 for ex in exercises if ex.get("status") == "success")
    failed = sum(1 for ex in exercises if ex.get("status") == "failure")
    score = (passed / total * 100) if total else 0.0
    typer.echo(f"{indent}Exercises: {total}")
    typer.secho(f"{indent}Passed: {passed}", fg=typer.colors.GREEN)
    typer.secho(f"{indent}Failed: {failed}", fg=typer.colors.RED)
    typer.echo(f"{indent}Score: {score:.1f}% ({passed}/{total})")


def status(
    all_classrooms: bool = typer.Option(
        False, "--all", help="Show stats for every classroom you belong to, not just the active one"
    ),
) -> None:
    """Show your login, active classroom, and exercise stats."""
    client = require_client()
    typer.echo(f"Logged in as: {config.get_username()}")

    try:
        classrooms = client.list_classrooms()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    active_slug = config.get_active_classroom()

    if all_classrooms:
        if not classrooms:
            typer.echo("You are not enrolled in any classrooms yet.")
            return
        for i, c in enumerate(classrooms):
            if i > 0:
                typer.echo()
            marker = "*" if c["slug"] == active_slug else " "
            typer.echo(f"{marker} {c['name']} ({c['slug']})")
            try:
                exercises = _fetch_exercises(c["slug"])
            except ApiError as e:
                typer.secho(f"    {e}", fg=typer.colors.RED)
                continue
            _print_stats(exercises, indent="    ")
        return

    if active_slug is None:
        typer.secho("No active classroom set. Run `eliude switch` first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    match = next((c for c in classrooms if c["slug"] == active_slug), None)
    if match is None:
        typer.secho(f"You are not enrolled in classroom '{active_slug}'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Classroom: {match['name']} ({match['slug']})")
    try:
        exercises = _fetch_exercises(active_slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    _print_stats(exercises)
