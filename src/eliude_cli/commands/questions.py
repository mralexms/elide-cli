from pathlib import Path

import typer

from .. import config
from ..client import ApiError
from ..session import require_practice_client

_STATUS_COLORS = {
    "success": typer.colors.GREEN,
    "failure": typer.colors.RED,
    "pending": typer.colors.YELLOW,
}


def list_questions(
    show_timestamp: bool = typer.Option(
        False, "--show-timestamp", help="Also show when you last submitted each question"
    ),
    unsolved: bool = typer.Option(
        False, "--unsolved", help="Only show questions you haven't passed yet (never submitted or failing)"
    ),
    tag: str = typer.Option(None, "--tag", help="Only show questions with this tag (e.g. vetores)"),
) -> None:
    """List the active practice's questions."""
    client = require_practice_client()
    try:
        questions = client.list_questions(tag=tag)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if unsolved:
        questions = [q for q in questions if q.get("status", "pending") != "success"]

    if not questions:
        typer.echo("No questions available.")
        return

    for q in questions:
        status = q.get("status", "pending")
        status_label = typer.style(f"{status:<8}", fg=_STATUS_COLORS.get(status))
        line = f"{q['slug']:<30} [{q['difficulty']:<6}] {status_label} {q['title']}"
        tags = q.get("tags") or []
        if tags:
            line += f"  [{', '.join(t['name'] for t in tags)}]"
        if show_timestamp:
            timestamp = q.get("last_submission_at") or "-"
            line += f"  (last submitted: {timestamp})"
        typer.echo(line)


def _format_caption(question: dict, classroom: str, practice: str, slug: str) -> str:
    """The question's title/statement as a C block comment, e.g. to paste at
    the top of a solution file."""
    lines = [
        "/*",
        f" * Classroom: {classroom}",
        f" * Practice: {practice}",
        f" * Question: {slug}",
        " *",
        f" * {question['title']}",
        " *",
    ]
    for line in question["statement"].splitlines():
        # Guard against the statement itself containing "*/", which would
        # otherwise prematurely close the comment block.
        lines.append(f" * {line}".replace("*/", "* /").rstrip())
    lines.append(" */")
    return "\n".join(lines)


def show_question(
    slug: str,
    download: bool = typer.Option(
        False, "--download", help="Also save the first sample test case as <slug>_input.txt / <slug>_output.txt"
    ),
    caption: bool = typer.Option(
        False, "--caption", help="Show only the title/statement, formatted as a C comment block"
    ),
    input_sample: bool = typer.Option(
        False, "--input-sample", help="Show only the first sample test case's input"
    ),
    output_sample: bool = typer.Option(
        False, "--output-sample", help="Show only the first sample test case's expected output"
    ),
) -> None:
    """Show a question's statement and sample test cases."""
    if sum([caption, input_sample, output_sample]) > 1:
        typer.secho("Use only one of --caption, --input-sample, --output-sample at a time.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    client = require_practice_client()
    try:
        question = client.get_question(slug)
    except ApiError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    samples = question.get("sample_test_cases", [])

    if caption:
        typer.echo(_format_caption(question, config.get_active_classroom(), config.get_active_practice(), slug))
        return

    if input_sample or output_sample:
        if not samples:
            typer.secho("No sample test case available.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        sample = samples[0]
        typer.echo(sample["stdin_data"] if input_sample else sample["expected_stdout"])
        return

    typer.secho(question["title"], bold=True)
    typer.echo(f"Difficulty: {question['difficulty']}")
    typer.echo(f"Time limit: {question['time_limit_seconds']}s  Memory limit: {question['memory_limit_mb']}MB")
    tags = question.get("tags") or []
    if tags:
        typer.echo(f"Tags: {', '.join(t['name'] for t in tags)}")
    typer.echo()
    typer.echo(question["statement"])

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
