import typer

from .messages import t


def normalize_newlines(text: str) -> str:
    # Test cases typed into the web portal may come with Windows line
    # endings (\r\n); the student should only ever see/get plain \n.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def echo_block(label: str, value: str, indent: int = 4, mark_trailing_spaces: bool = False) -> bool:
    """Prints a test case's input/output as the lines it really is, indented
    under its label, instead of a Python repr full of \n/\r\n escapes.

    With mark_trailing_spaces, spaces/tabs at the end of a line show as a
    dim ·/→ (otherwise invisible, and sometimes the reason a case failed).
    Returns whether any were marked.
    """
    pad = " " * indent
    typer.echo(f"{pad}{label}")
    text = normalize_newlines(value).rstrip("\n")
    if not text:
        typer.secho(f"{pad}  {t('questions.empty_value')}", dim=True)
        return False
    marked = False
    for line in text.split("\n"):
        body = line.rstrip(" \t") if mark_trailing_spaces else line
        trailing = line[len(body):]
        if trailing:
            marked = True
            trailing = typer.style(trailing.replace(" ", "·").replace("\t", "→"), dim=True)
        typer.echo(f"{pad}  {body}{trailing}")
    return marked


def print_submission_result(data: dict) -> None:
    status = data["status"]

    if status == "compile_error":
        typer.secho(t("submission.compilation_failed"), fg=typer.colors.RED, bold=True)
        typer.echo(data.get("compile_output", "").rstrip("\n"))
        return

    result = data.get("result_detail", {})
    test_cases = result.get("test_cases", [])
    for i, tc in enumerate(test_cases, start=1):
        if tc.get("passed"):
            typer.secho(t("submission.test_case_pass", n=i), fg=typer.colors.GREEN)
        else:
            reason = tc.get("reason") or t("submission.reason_failed")
            typer.secho(t("submission.test_case_fail", n=i, reason=reason), fg=typer.colors.RED)
            if tc.get("is_sample"):
                marked = False
                if "stdin_data" in tc:
                    echo_block(t("submission.stdin_label"), tc["stdin_data"], indent=2)
                if "expected_stdout" in tc:
                    marked |= echo_block(t("submission.expected_label"), tc["expected_stdout"], indent=2, mark_trailing_spaces=True)
                if "stdout" in tc:
                    marked |= echo_block(t("submission.actual_label"), tc["stdout"], indent=2, mark_trailing_spaces=True)
                if tc.get("stderr"):
                    echo_block(t("submission.stderr_label"), tc["stderr"], indent=2)
                if marked:
                    typer.secho(f"  {t('submission.trailing_space_legend')}", dim=True)

    ai_check = result.get("ai_check")
    criteria_not_met = bool(ai_check) and not ai_check.get("criteria_met", True)
    if criteria_not_met:
        typer.secho(t("submission.criteria_not_met"), fg=typer.colors.RED, bold=True)
        typer.echo(f"  {ai_check.get('feedback', '')}")

    passed_count = result.get("passed_count", 0)
    total_count = result.get("total_count", 0)
    color = typer.colors.GREEN if status == "passed" else typer.colors.RED
    summary = t("submission.result_summary", passed=passed_count, total=total_count)
    if criteria_not_met:
        summary += t("submission.but_criteria_not_met")
    typer.secho(summary, fg=color, bold=True)
