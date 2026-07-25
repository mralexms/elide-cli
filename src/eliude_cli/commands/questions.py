from pathlib import Path

import typer

from .. import config
from ..client import ApiError
from ..messages import t
from ..session import require_practice_client

_STATUS_COLORS = {
    "success": typer.colors.GREEN,
    "failure": typer.colors.RED,
    "pending": typer.colors.YELLOW,
}


def list_questions(
    show_timestamp: bool = typer.Option(False, "--show-timestamp", help=t("help.opt.questions_show_timestamp")),
    unsolved: bool = typer.Option(False, "--unsolved", help=t("help.opt.questions_unsolved")),
    tag: str = typer.Option(None, "--tag", help=t("help.opt.questions_tag")),
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
        typer.echo(t("questions.no_questions"))
        return

    for q in questions:
        status = q.get("status", "pending")
        status_label = typer.style(f"{status:<8}", fg=_STATUS_COLORS.get(status))
        line = f"{q['slug']:<30} [{q['difficulty']:<6}] {status_label} {q['title']}"
        tags = q.get("tags") or []
        if tags:
            line += f"  [{', '.join(tag['name'] for tag in tags)}]"
        if show_timestamp:
            timestamp = q.get("last_submission_at") or "-"
            line += f"  ({t('questions.last_submitted', timestamp=timestamp)})"
        typer.echo(line)


def _format_caption(question: dict, classroom: str, practice: str, slug: str) -> str:
    """The question's title/statement as a C block comment, e.g. to paste at
    the top of a solution file."""
    lines = [
        "/*",
        f" * {t('questions.caption_classroom', classroom=classroom)}",
        f" * {t('questions.caption_practice', practice=practice)}",
        f" * {t('questions.caption_question', slug=slug)}",
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
    download: bool = typer.Option(False, "--download", help=t("help.opt.show_download")),
    caption: bool = typer.Option(False, "--caption", help=t("help.opt.show_caption")),
    input_sample: bool = typer.Option(False, "--input-sample", help=t("help.opt.show_input_sample")),
    output_sample: bool = typer.Option(False, "--output-sample", help=t("help.opt.show_output_sample")),
) -> None:
    """Show a question's statement and sample test cases."""
    if sum([caption, input_sample, output_sample]) > 1:
        typer.secho(t("questions.only_one_display_flag"), fg=typer.colors.RED)
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
            typer.secho(t("questions.no_sample"), fg=typer.colors.RED)
            raise typer.Exit(code=1)
        sample = samples[0]
        typer.echo(sample["stdin_data"] if input_sample else sample["expected_stdout"])
        return

    typer.secho(question["title"], bold=True)
    typer.echo(t("questions.difficulty_label", difficulty=question["difficulty"]))
    typer.echo(
        t("questions.limits_label", time=question["time_limit_seconds"], memory=question["memory_limit_mb"])
    )
    tags = question.get("tags") or []
    if tags:
        typer.echo(t("questions.tags_label", tags=", ".join(tag["name"] for tag in tags)))
    typer.echo()
    typer.echo(question["statement"])

    if samples:
        typer.echo()
        typer.secho(t("questions.sample_test_cases_header"), bold=True)
        for tc in samples:
            typer.echo(f"  {t('questions.input_label', value=repr(tc['stdin_data']))}")
            typer.echo(f"  {t('questions.expected_label', value=repr(tc['expected_stdout']))}")

    if download:
        if not samples:
            typer.secho(t("questions.no_sample_to_download"), fg=typer.colors.YELLOW)
            return
        sample = samples[0]
        input_path = Path(f"{slug}_input.txt")
        output_path = Path(f"{slug}_output.txt")
        input_path.write_text(sample["stdin_data"])
        output_path.write_text(sample["expected_stdout"])
        typer.secho(t("questions.saved_sample", input_path=input_path, output_path=output_path), fg=typer.colors.GREEN)
