from pathlib import Path

import typer

from ..client import ApiError
from ..session import require_practice_client

_STATUS_COLORS = {
    "success": typer.colors.GREEN,
    "failure": typer.colors.RED,
    "pending": typer.colors.YELLOW,
}


def list_exercises(
    show_timestamp: bool = typer.Option(
        False, "--show-timestamp", help="Also show when you last submitted each exercise"
    ),
    unsolved: bool = typer.Option(
        False, "--unsolved", help="Only show exercises you haven't passed yet (never submitted or failing)"
    ),
    tag: str = typer.Option(None, "--tag", help="Only show exercises with this tag (e.g. vetores)"),
) -> None:
    """List the active practice's questions."""
    client = require_practice_client()
    try:
        exercises = client.list_exercises(tag=tag)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if unsolved:
        exercises = [ex for ex in exercises if ex.get("status", "pending") != "success"]

    if not exercises:
        typer.echo("No exercises available.")
        return

    for ex in exercises:
        status = ex.get("status", "pending")
        status_label = typer.style(f"{status:<8}", fg=_STATUS_COLORS.get(status))
        line = f"{ex['slug']:<30} [{ex['difficulty']:<6}] {status_label} {ex['title']}"
        tags = ex.get("tags") or []
        if tags:
            line += f"  [{', '.join(t['name'] for t in tags)}]"
        if show_timestamp:
            timestamp = ex.get("last_submission_at") or "-"
            line += f"  (last submitted: {timestamp})"
        typer.echo(line)


def show_exercise(
    slug: str,
    download: bool = typer.Option(
        False, "--download", help="Also save the first sample test case as <slug>_input.txt / <slug>_output.txt"
    ),
) -> None:
    """Show a question's statement and sample test cases."""
    client = require_practice_client()
    try:
        exercise = client.get_exercise(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(exercise["title"], bold=True)
    typer.echo(f"Difficulty: {exercise['difficulty']}")
    typer.echo(f"Time limit: {exercise['time_limit_seconds']}s  Memory limit: {exercise['memory_limit_mb']}MB")
    tags = exercise.get("tags") or []
    if tags:
        typer.echo(f"Tags: {', '.join(t['name'] for t in tags)}")
    typer.echo()
    typer.echo(exercise["statement"])

    samples = exercise.get("sample_test_cases", [])
    if samples:
        typer.echo()
        typer.secho("Sample test cases:", bold=True)
        for tc in samples:
            typer.echo(f"  Input:    {tc['stdin_data']!r}")
            typer.echo(f"  Expected: {tc['expected_stdout']!r}")

    if download:
        if not samples:
            typer.secho("No sample test case available to download.", fg=typer.colors.YELLOW)
            return
        sample = samples[0]
        input_path = Path(f"{slug}_input.txt")
        output_path = Path(f"{slug}_output.txt")
        input_path.write_text(sample["stdin_data"])
        output_path.write_text(sample["expected_stdout"])
        typer.secho(f"Saved sample test case to {input_path} and {output_path}.", fg=typer.colors.GREEN)
