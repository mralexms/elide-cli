import typer

from .messages import t


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
                if "stdin_data" in tc:
                    typer.echo(f"  {t('submission.stdin_label')}: {tc['stdin_data']!r}")
                if "expected_stdout" in tc:
                    typer.echo(f"  {t('submission.expected_label')}: {tc['expected_stdout']!r}")
                if "stdout" in tc:
                    typer.echo(f"  {t('submission.actual_label')}: {tc['stdout']!r}")
                if tc.get("stderr"):
                    typer.echo(f"  {t('submission.stderr_label')}: {tc['stderr']!r}")

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
