import typer

from ..client import ApiError
from ..session import require_client


def list_exercises() -> None:
    """List available exercises."""
    client = require_client()
    try:
        exercises = client.list_exercises()
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not exercises:
        typer.echo("No exercises available.")
        return

    for ex in exercises:
        typer.echo(f"{ex['slug']:<30} [{ex['difficulty']:<6}] {ex['title']}")


def show_exercise(slug: str) -> None:
    """Show an exercise's statement and sample test cases."""
    client = require_client()
    try:
        exercise = client.get_exercise(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(exercise["title"], bold=True)
    typer.echo(f"Difficulty: {exercise['difficulty']}")
    typer.echo(f"Time limit: {exercise['time_limit_seconds']}s  Memory limit: {exercise['memory_limit_mb']}MB")
    typer.echo()
    typer.echo(exercise["statement"])

    samples = exercise.get("sample_test_cases", [])
    if samples:
        typer.echo()
        typer.secho("Sample test cases:", bold=True)
        for tc in samples:
            typer.echo(f"  Input:    {tc['stdin_data']!r}")
            typer.echo(f"  Expected: {tc['expected_stdout']!r}")
